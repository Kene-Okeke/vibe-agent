import zipfile
import json
from vibe_agent.manifest import Manifest

MAX_FILES= 2000
MAX_TOTAL_SIZE=200 * 1024 * 1024 #200MB

FOLDERS_TO_SKIP =[
    "__MACOSX", "node_modules", ".git", ".venv", "venv",
         "dist", "build", ".next", "out", "__pycache__," "vendor"
]

def is_junk_folder(name: str ) -> bool:

    for piece in name.split("/"):
        if piece in FOLDERS_TO_SKIP:
            return True
    return False

    

     
MARKERS = {
    "package.json": "node",
    "requirements.txt": "python",
    "pyproject.toml": "python",
    "index.html": "static",
}

def list_zip_files( path: str ):
    with zipfile.ZipFile(path) as zip_file:

        files_in_zipfile = zip_file.infolist()
        if len(files_in_zipfile) > MAX_FILES:
            raise ValueError("ZIP has too many files")

        total_file_size = 0
        for file in files_in_zipfile:
            total_file_size  += file.file_size 

        if total_file_size > MAX_TOTAL_SIZE:
            raise ValueError("ZIP is too big when unzipped")
        
        list_of_file_paths = []
        for file in files_in_zipfile:
            name = file.filename
            if name.startswith("/"):
                raise ValueError(f"Unsafe path in ZIP: {name}")
            elif ".." in name.split("/"):
                raise ValueError(f"Unsafe path in ZIP: {name}")
            elif file.is_dir():
                continue
            else:
                list_of_file_paths.append(name)
            

    return list_of_file_paths


def choose_app_type(app_types : list[str]):
    if "node" in app_types and "python" in app_types:
        return None
    elif "node" in app_types:
        return "node"
    elif "python" in app_types:
        return "python"
    else:
        return "static"


def find_apps(file_names: list[str], workspace_roots: list[str] | None = None):
    if workspace_roots is None:
        workspace_roots = []
    marker_files = []
    for name in file_names:
        if is_junk_folder(name):
            continue

        file = name.split("/")[-1]

        if file in MARKERS:
            folder = name.removesuffix(file)

            found = {
                "folder":folder,
                "app_type":MARKERS[file]
            }

            marker_files.append(found) # builds marker files

    if not marker_files:
        raise ValueError("Can't tell what kind of app this is") 


    folders = []
    for item in marker_files:
        if item["folder"] not in folders:
            folders.append(item["folder"]) # creates a folders list for only one instance of the same folder 
    


    services =[]
    for folder in folders:
        types = []
        for item in marker_files:
            if item["folder"] == folder:
                types.append(item["app_type"])

        services.append({"folder": folder, "app_type": choose_app_type(types)}) # creates a list of services(folder and app type) and chooses app type based on choose_app_type function
    

    
    apps =[]
    for service in services:
        if service["folder"] in workspace_roots:
            continue
        apps.append(service)
    services=apps

    result = []
    for service in services:
        inside_another = False
        if service["app_type"]!= "static":
            result.append(service)
            continue
        for parent_directory in services:
                if service["folder"] != parent_directory["folder"]:
                    if service["folder"].startswith(parent_directory["folder"]):
                        inside_another = True
                        break

        if not inside_another:
            result.append(service) # services(folder and app type ) where the folders are not inside another folder

    return result

def find_workspace_roots(path: str, names: list[str]):
    workspace_roots = []
    with zipfile.ZipFile(path) as zip_file:
        for name in names:
            if is_junk_folder(name):
                continue

            file =  name.split("/")[-1]
            folder = name.removesuffix(file)
            if file == "pnpm-workspace.yaml":
                workspace_roots.append(folder)

            if file == "package.json":
                raw_bytes = zip_file.read(name)
            
                try:
                    text = raw_bytes.decode()
                    data = json.loads(text)
                except ValueError:
                    continue

                if "workspaces" in data:

                    workspace_roots.append(folder)

    return workspace_roots

def find_one_workspace_root( app: dict, roots: list[str] ) -> str | None:
    if app["app_type"]!= "node":
        return None

    for root in roots:
        if app["folder"].startswith(root):
            return root

    return None  


NODE_LOCK_FILES = ["package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb", "bun.lock"]
PYTHON_LOCK_FILES = ["poetry.lock", "uv.lock"]
def find_lockfile( app: dict, names: list[str])  -> str | None:
    #  set up from the app's type
    if app["app_type"] == "node":
        lock_files = NODE_LOCK_FILES
                  
    elif app["app_type"] == "python":
        lock_files = PYTHON_LOCK_FILES
                 
    elif app["app_type"] == "static":
        return None
    else:
        lock_files = NODE_LOCK_FILES + PYTHON_LOCK_FILES            

    
    for name in names:
        if is_junk_folder(name):
            continue
        file = name.split("/")[-1]
        if file not in lock_files:
            continue
        folder = name.removesuffix(file)
        if folder == app["folder"]:
            return file

    #  a lock file in a folder ABOVE the app? (monorepo root)
    for name in names:
        if is_junk_folder(name):
            continue
        file = name.split("/")[-1]
        if file not in lock_files:
            continue
        folder = name.removesuffix(file)
        if app["folder"].startswith(folder):
            return file
    return None

# app = {"folder": "vibe-deploy/frontend/", "app_type": "node", "lockfile": "package-lock.json"}

# app["folder"]       # 'vibe-deploy/frontend/'
# app["app_type"]     # 'node'
# app["lockfile"]     # 'package-lock.json'

def add_lockfiles(apps: list[dict], names: list[str]):
    for app in apps:
        app["lockfile"] = find_lockfile(app,names)
    return apps



def read_packages(path: str, names: list[str]):
    packages = []
    with zipfile.ZipFile(path) as zip_file:
        for name in names:
            if is_junk_folder(name):
                continue
            file = name.split("/")[-1]
            if file != "package.json":
                continue

            folder = name.removesuffix(file)
            raw_bytes = zip_file.read(name)
            

            try:
                text = raw_bytes.decode()
                data = json.loads(text)
            except ValueError:
                continue

            if "name" not in data:
                continue

            
            uses=[]
            if "dependencies" in data:
                for dependency in data["dependencies"]:
                    uses.append(dependency)
            if "devDependencies" in data:
                for dependency in data["devDependencies"]:
                    uses.append(dependency)

            packages.append({"folder": folder, "name": data["name"], "uses": uses})
    return packages

def find_libraries(packages: list[dict]):
    libraries = []
    for package in packages:
        for other_package in packages:
            if other_package["folder"] != package["folder"] and package["name"] in other_package["uses"]:
                if package["folder"] not in libraries:
                    libraries.append(package["folder"])
    return libraries

def find_local_packages(app: dict, packages: list[dict] )  -> list[str]:
    uses = []
    for package in packages:
        if package["folder"]==app["folder"]:
            uses.append(package["uses"])

    local_packages = []
    for package in packages:
        if package["name"] in uses:
            local_packages.append(package["folder"])

    return local_packages


def add_monorepo_info(apps: list[dict], roots: list[str], packages: list[dict] ) -> list[dict]:
    for app in apps:
        app["workspace_root"] = find_one_workspace_root(app, roots)
        app["local_packages"] = find_local_packages(app, packages)
    return apps
    
def is_secret(file:str) -> bool:
    if file == ".env" or file.startswith(".env."):
        return True
    return False


MAX_FILES_LISTED = 500 
def find_app_files(app: dict, names: list[str] ) -> list[str]:
    files = []
    for name in names:
        if is_junk_folder(name):
            continue
        if not name.startswith(app["folder"]):
            continue
        file = name.split("/")[-1]
        if is_secret(file) == True:
            continue
 
        files.append(name.removeprefix(app["folder"]))
        if len(files)==MAX_FILES_LISTED:
            break

    return files

EVIDENCE_FILES = ["package.json", "requirements.txt", "pyproject.toml", "index.html", ".nvmrc", ".python-version"]
def is_marker(file: str) -> bool:
    if file in EVIDENCE_FILES or  file in NODE_LOCK_FILES or  file in PYTHON_LOCK_FILES:
        return True
    if file.startswith("vite.config.") or file.startswith("next.config."):
        return True

    return False


def find_markers(files: list[str] ) -> list[str]:
    markers = []
    for file in files:
        if "/" in file:
            continue
        if is_marker(file):
            markers.append(file)
    return markers


FILES_TO_READ = ["package.json", "requirements.txt", "pyproject.toml", ".nvmrc", ".python-version"]
MAX_MARKER_BYTES = 64 * 1024

def should_read(file: str ) -> bool:

    if file in FILES_TO_READ:
        return True
    if file.startswith("vite.config.") or file.startswith("next.config."):
        return True
    return False


def read_marker_files( app: dict, path: str, markers: list[str] ) -> dict[str, str]:
    marker_files={}
    with zipfile.ZipFile(path) as zip_file:
        for marker in markers:
            if not should_read(marker):
                continue

            raw_bytes = zip_file.read(app["folder"] + marker)
            if len(raw_bytes) > MAX_MARKER_BYTES:
                continue
            try:
                text = raw_bytes.decode()
            except ValueError:
                continue

            marker_files[marker]=text

    return marker_files


def build_manifest( app: dict, path: str, names: list[str] ) -> Manifest:

    files = find_app_files(app, names)
    markers = find_markers(files)
    marker_files = read_marker_files(app, path, markers)
    return Manifest(
        folder = app["folder"],
        markers=markers,
        marker_files=marker_files,
        files = files,
        lockfile=app['lockfile'],
        workspace_root=app['workspace_root'],
        shared_packages = app['local_packages'],
        app_type=app['app_type']
    )


             


    




