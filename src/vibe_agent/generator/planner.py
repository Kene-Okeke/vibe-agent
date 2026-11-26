import json
import re
import os 
from vibe_agent.manifest import Manifest
from vibe_agent.generator.build_plan import BuildPlan
from vibe_agent.llm import ask_llm
from vibe_agent.generator.llm_fallback import build_llm_prompt

FRAMEWORK_BY_PACKAGE = {
    "next": "next",
    "vite": "vite",
    "express": "node-server",
    "fastify": "node-server",
    "@nestjs/core": "node-server",
    "koa": "node-server",
    "hono": "node-server",
}

LOCKFILE_TO_MANAGER = {
    "package-lock.json": "npm",
    "pnpm-lock.yaml": "pnpm",
    "yarn.lock": "yarn",
    "uv.lock": "uv",
    "poetry.lock": "poetry",
   "bun.lock": "bun",
    "bun.lockb": "bun",
}

INSTALL_WITH_LOCKFILE = {
    "npm": "npm ci",
    "pnpm": "pnpm install --frozen-lockfile",
    "yarn": "yarn install --immutable",
    "bun": "bun install --frozen-lockfile",
    "pip": "pip install --no-cache-dir -r requirements.txt",
    "uv": "uv sync --frozen",
    "poetry": "poetry install --no-root",
}

INSTALL_WITHOUT_LOCKFILE = {
    "npm": "npm install",
    "pnpm": "pnpm install",
    "yarn": "yarn install",
    "bun": "bun install",
    "pip": "pip install --no-cache-dir -r requirements.txt",
    "uv": "uv sync",
    "poetry": "poetry install --no-root",
}

RUN_SCRIPT = {
    "npm": "npm run",
    "pnpm": "pnpm run",
    "yarn": "yarn",
    "bun": "bun run",
}

# how each package manager runs a package's tool directly (no script needed)
EXEC_TOOL = {
    "npm": "npx",
    "pnpm": "pnpm exec",
    "yarn": "yarn",
    "bun": "bunx",
}

FASTAPI_MODULES = {
    "main.py": "main",
    "app/main.py": "app.main",
    "src/main.py": "src.main",
    "app.py": "app",
}

# where Flask apps usually live → the module gunicorn should load
FLASK_MODULES = {
    "app.py": "app",
    "wsgi.py": "wsgi",
    "main.py": "main",
    "app/__init__.py": "app",
}

# words that mean "development mode": never used in production
DEV_WORDS = ["nodemon", "--watch", "--reload", "next dev"]

NODE_ENTRY_FILES = ["server.js", "index.js", "app.js", "src/server.js", "src/index.js"]

UNKNOWN = "unknown"

PORT_BY_FRAMEWORK = {
    "next": 3000,          # Next.js default
    "node-server": 3000,   # common Express default
    "fastapi": 8000,       # must match --port 8000 in the uvicorn command
    "vite": 80,            # Caddy serves the built files on port 80
    "static": 80,          # same: Caddy
    "flask": 5000,         
}

DEFAULT_RUNTIME = {
    "node": "22",
    "python": "3.12",
    "bun": "1",
}

def read_package_json(manifest: Manifest) -> dict:
    text = manifest.marker_files.get("package.json")
    if text is None:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def read_requirements_txt(manifest: Manifest) ->list[str]:
    text = manifest.marker_files.get("requirements.txt")
    if text is None:
        return []
    
    names = []

    #now we go through each line
    for line in text.splitlines():
        line = line.strip()

        if not line or line.startswith("#") or line.startswith("-"):
            continue
        
        match = re.match(r"[A-Za-z0-9_.\-]+", line) 
            #this is called regex we check each line 
            #and return on the characters within the square brackets and cuts of at anything thats not there
        
        if match:
            names.append(match.group(0).lower())
    return names

def workspace_app_path(manifest: Manifest) -> str | None:
    # normal app → None; monorepo app → its path from the workspace root, e.g. "apps/web"
    if manifest.workspace_root is None:
        return None
    app_path = os.path.relpath(manifest.folder, manifest.workspace_root)
    if app_path == ".":
        return None          # the app IS the root, so treat it like a normal app
    return app_path

def detect_framework(manifest: Manifest) -> str | None:
    #framework: Literal["next", "vite", "node-server", "fastapi", "static"]
    package_json = read_package_json(manifest)
    if package_json:
        dependencies = package_json.get("dependencies", {})| package_json.get("devDependencies",{}) 
            # | means join dependecies and devDependencies 
        
        for package_name, framework in FRAMEWORK_BY_PACKAGE.items():
            if package_name in dependencies:
                return framework
    
    # Python rules will go here (after read_requirements(using a seperate function for read requirements.txt))
    requirements = read_requirements_txt(manifest)
    if "fastapi" in requirements:
        return "fastapi"

    if "flask" in requirements:          # ← add
        return "flask"
    
    if manifest.app_type == "static":
        return "static"

    #if nothing matched then return none 
    return UNKNOWN


def detect_package_manager(manifest:Manifest) -> str | None:
    if manifest.lockfile in LOCKFILE_TO_MANAGER:
        return LOCKFILE_TO_MANAGER[manifest.lockfile]

    # 3. defaults by app type
    if manifest.app_type == "node":
        return "npm"

    if manifest.app_type == "python":
        return "pip"

    if manifest.app_type == "static":
        return None

    return UNKNOWN #llm comes in if the funciton reaches unknown


def pick_install_command(package_manager: str | None, has_lockfile: bool) -> str | None:
    # static site: nothing to install
    if package_manager is None:
        return None

    # unknown package manager: can't pick a command
    if package_manager == UNKNOWN:
        return UNKNOWN

    # lockfile exists: strict install (exact versions)
    if has_lockfile:
        return INSTALL_WITH_LOCKFILE.get(package_manager, UNKNOWN)

    # no lockfile: relaxed install
    return INSTALL_WITHOUT_LOCKFILE.get(package_manager, UNKNOWN)


def detect_build_command(manifest: Manifest, framework: str, package_manager: str | None) -> str | None:
    if framework == UNKNOWN:
        return UNKNOWN

    if framework in ["static", "fastapi", "flask"]:
        return None

    scripts = read_package_json(manifest).get("scripts", {})
    app_path = workspace_app_path(manifest)

    # monorepo app: build THIS workspace, while standing at the workspace root
    if app_path is not None:
        if package_manager != "npm":
            return UNKNOWN          # v1: only npm workspaces; the LLM fallback can try the rest
        if "build" in scripts:
            return f"npm run build -w {app_path}"
        if framework in ["next", "vite"]:
            return f"npm exec -w {app_path} -- {framework} build"
        return None

    # normal app (unchanged from before)
    if "build" in scripts:
        return f"{RUN_SCRIPT.get(package_manager, 'npm run')} build"

    if framework in ["next", "vite"]:
        return f"{EXEC_TOOL.get(package_manager, 'npx')} {framework} build"

    return None
# this check is for the llm , start command is something that could be wrong and we have to check 
# if the js file exists in the file path - thisb lets us know if the llm really got the strat command to prevent crashes 

def start_file_exists(manifest: Manifest, start_command: str) -> bool:
    for word in start_command.split():
        if word.endswith(".js"):
            # found the filename: is it really in the project?
            if word in manifest.files:
                return True      # case 1: file exists ✅
            else:
                return False     # case 2: file made up ❌

    # case 3: no .js word at all (e.g. "npm run start"), nothing to check
    return True

def check_llm_answers(manifest: Manifest, llm_answers: dict, unknowns:list[str]) -> dict:
   # 1. keep ONLY the fields we asked for, and make sure each one was answered
   checked = {}
   for name in unknowns:
    if name not in llm_answers:
        raise ValueError(f"LLM didn't answer: {name}")
    checked[name] = llm_answers[name]

    # 2. if the LLM gave a start command, it must be production-safe and real
    start_command = checked.get("start_command")
    if start_command:
        if is_dev_command(start_command):
            raise ValueError(f"LLM gave a dev command: {start_command}")
        if not start_file_exists(manifest, start_command):
            raise ValueError(f"LLM named a file that doesn't exist: {start_command}")

    # 3. passed every check: safe to use
    return checked

def fill_unknowns_with_llm(manifest: Manifest,answers:dict, unknowns:list[str]) -> dict:
    # ask the LLM; a timeout or network error means it couldn't help
    try:
        prompt = build_llm_prompt(manifest,answers,unknowns)
        llm_answers = ask_llm(prompt)
    except Exception as error:
       raise ValueError(f"Couldn't work out: {', '.join(unknowns)} (LLM unavailable: {error})")

    # judge the reply (raises ValueError if it's wrong)
    checked = check_llm_answers(manifest, llm_answers, unknowns)

       # the rules' answers, with the gaps filled in
    return answers | checked



def detect_start_command(manifest: Manifest, framework:str, package_manager: str | None) -> str | None:
    if framework == UNKNOWN:
        return UNKNOWN

    if framework in ["vite", "static"]:
        return None
    
    scripts = read_package_json(manifest).get("scripts", {})

    if framework == "next":
        if "start" in scripts:
            return f"{RUN_SCRIPT.get(package_manager,'npm run')} start"
        return f"{EXEC_TOOL.get(package_manager,'npx')} next start"
     
    if framework == "fastapi":
        for path, module in FASTAPI_MODULES.items():
            if path in manifest.files:
                return f"uvicorn {module}:app --host 0.0.0.0 --port 8000"
        return UNKNOWN
    
    if framework == "flask":
        for path, module in FLASK_MODULES.items():
            if path in manifest.files:
                return f"gunicorn {module}:app --bind 0.0.0.0:5000"
        return UNKNOWN

    if framework == "node-server":
        if "start" in scripts and not is_dev_command(scripts["start"]):
            return f"{RUN_SCRIPT.get(package_manager, 'npm run')} start"
        
        # ↓ only reached if the line above did NOT return, so it works like "else"
        dev_script = scripts.get("dev", "")
        for word in dev_script.split():
            if word.endswith(".js"):
                return f"node {word}"

        # ↓ only reached if no .js file was in the dev script
        for name in NODE_ENTRY_FILES:
            if name in manifest.files:
                return f"node {name}"

         # ↓ only reached if none of the common files exist
        return UNKNOWN

    return UNKNOWN
 
def detect_port(framework: str) -> int | str:
    # look up the framework's port; UNKNOWN if it's not in the table
    return PORT_BY_FRAMEWORK.get(framework, UNKNOWN)

def detect_output_dir(manifest: Manifest, framework: str) -> str | None:
    if framework == "static":
        return "."

    if framework != "vite":
        return None

    # Vite: a custom outDir from its config, otherwise "dist"
    out = "dist"
    for name in ["vite.config.ts", "vite.config.js", "vite.config.mjs"]:
        config = manifest.marker_files.get(name)
        if config:
            match = re.search(r"outDir\s*:\s*['\"]([^'\"]+)['\"]", config)
            if match:
                out = match.group(1)
                break

    # monorepo app: the output sits INSIDE the app's folder
    app_path = workspace_app_path(manifest)
    if app_path is not None:
        return f"{app_path}/{out}"
    return out



def detect_runtime_version(manifest: Manifest, framework: str, package_manager: str | None) -> str | None:
    # can't tell what the app is → can't tell what it runs on
    if framework == UNKNOWN:
        return UNKNOWN

    # static: nothing runs, so no runtime needed
    if framework == "static":
        return None

    # Bun apps run on Bun, not Node
    if package_manager == "bun":
        return DEFAULT_RUNTIME["bun"]

    # Python: .python-version if the project has one, otherwise the default
    if framework in ["fastapi", "flask"]:
        pinned = manifest.marker_files.get(".python-version")
        if pinned:
            return pinned.strip()
        return DEFAULT_RUNTIME["python"]

    # everything else runs on Node: .nvmrc if present, otherwise the default
    pinned = manifest.marker_files.get(".nvmrc")
    if pinned:
        return pinned.strip().removeprefix("v")
    return DEFAULT_RUNTIME["node"]


def make_build_plan(manifest: Manifest) -> BuildPlan:
    # 1. what kind of app is this?
    framework = detect_framework(manifest)

    # 2. how are its packages installed?
    package_manager = detect_package_manager(manifest)
    has_lockfile = manifest.lockfile is not None
    install_command = pick_install_command(package_manager, has_lockfile)

    # 3. how is it built and started?
    build_command = detect_build_command(manifest, framework, package_manager)
    start_command = detect_start_command(manifest, framework, package_manager)

    # 4. where are the built files, which port, which runtime?
    output_dir = detect_output_dir(manifest, framework)
    port = detect_port(framework)
    runtime_version = detect_runtime_version(manifest, framework, package_manager)


    answers = {
        "framework": framework,
        "install_command": install_command,
        "build_command": build_command,
        "start_command": start_command,
        "port": port,
        "runtime_version": runtime_version,
    }

    unknowns = []
    for name, value in answers.items():
        if value == UNKNOWN:
            unknowns.append(name)

    # 6. everything decided by rules, so we're confident
    confidence = "high"

    if unknowns:
       answers = fill_unknowns_with_llm(manifest,answers, unknowns)
       confidence = "medium"

       output_dir = detect_output_dir(manifest, answers["framework"])

    # 7. create the plan: pydantic checks every field here
    return BuildPlan(
        framework=answers["framework"],
        runtime_version=answers["runtime_version"],
        package_manager=package_manager,
        has_lockfile=has_lockfile,
        install_command=answers["install_command"],
        build_command=answers["build_command"],
        start_command=answers["start_command"],
        output_dir=output_dir,
        port=answers["port"],
        confidence=confidence,
    )