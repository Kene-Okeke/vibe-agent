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

