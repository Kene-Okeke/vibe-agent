import zipfile
import json

MAX_FILES= 2000
MAX_TOTAL_SIZE=200 * 1024 * 1024 #200MB

FOLDERS_TO_SKIP =[
    "__MACOSX", "node_modules", ".git", ".venv", "venv",
         "dist", "build", ".next", "out", "__pycache__"
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
    if "node" in app_types:
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

NODE_LOCKS = {
    "package-lock.json": "npm",
    "yarn.lock": "yarn",
    "pnpm-lock.yaml": "pnpm",
    "bun.lockb": "bun",
    "bun.lock": "bun",
}
PYTHON_LOCKS = {
    "poetry.lock": "poetry",
    "uv.lock": "uv",
}

def find_package_manager(app: dict, names: list[str]):
    #  set up from the app's type
    if app["app_type"] == "node":
        lock_files = NODE_LOCKS
        manager = "npm"            # the guess
    elif app["app_type"] == "python":
        lock_files = PYTHON_LOCKS
        manager = "pip"            # the guess
    else:
        return "none"              # static: nothing to install

    #  a lock file in the app's own folder?
    for name in names:
        if is_junk_folder(name):
            continue
        file = name.split("/")[-1]
        if file not in lock_files:
            continue
        folder = name.removesuffix(file)
        if folder == app["folder"]:
            return lock_files[file]

    #  a lock file in a folder ABOVE the app? (monorepo root)
    for name in names:
        if is_junk_folder(name):
            continue
        file = name.split("/")[-1]
        if file not in lock_files:
            continue
        folder = name.removesuffix(file)
        if app["folder"].startswith(folder):
            return lock_files[file]
    return manager


def add_package_managers(apps: list[dict], names: list[str]):
    for app in apps:
        app["package_manager"] = find_package_manager(app,names)
    return apps



def find_libraries(path: str, names: list[str]):
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

    libraries = []

    for package in packages:
        for other_package in packages:
            if other_package["folder"] != package["folder"] and package["name"] in other_package["uses"]:
                if package["folder"] not in libraries:
                    libraries.append(package["folder"])
    return libraries

            
                



             


    




