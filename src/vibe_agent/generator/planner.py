import json
import re
from vibe_agent.manifest import Manifest

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
    "bun.lock": "npm",       
    "bun.lockb": "npm",
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



def detect_framework(manifest: Manifest) -> str | None:
    #framework: Literal["next", "vite", "node-server", "fastapi", "static"]
    package_json = read_package_json(manifest)
    if package_json:
        dependecies = package_json.get("dependencies",{})| package_json.get("devDependencies",{}) 
            # | means join dependecies and devDependencies 
        
        for package_name, framework in FRAMEWORK_BY_PACKAGE.items():
            if package_name in dependencies:
                return framework
    
    # Python rules will go here (after read_requirements(using a seperate function for read requirements.txt))
    requirements = read_requirements_txt(manifest)
    if "fastapi" in requirements:
        return "fastapi"
    
    if manifest.app_type == "static":
        return "static"

    #if nothing matched then return none 
    return None


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


def detect_build_command(manifest: Manifest, 
:str , package_manager: str|None) -> str | None:
    if framework == UNKNOWN:
        return UNKNOWN
    
    if framework in ["static" , "fastapi"]:
        return None

    # 3. get the scripts from package.json - using the read_package_json function
    scripts = read_package_json(manifest).get("scripts",{})

     # 4. if it has a "build" script: run it by name with the right package manager
    if "build" in scripts:
            return f"{RUN_SCRIPT.get(package_manager,'npm run')} build"

    if framework in ["next", "vite"]:
        return f"{EXEC_TOOL.get(package_manager, 'npx')}{framework} build"

    # 6. anything else (node-server with no build script): no build step
    return None

def is_dev_command(command: str) -> bool:
    for word in DEV_WORDS:
        if word in command:
            return True
    return False


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
 