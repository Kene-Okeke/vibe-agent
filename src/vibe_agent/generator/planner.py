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


UNKNOWN = "unknown"

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

    return UNKNOWN


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


def detect_build_command(manifest: Manifest, framework:str , package_manager: str|None) -> str | None:
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

    
