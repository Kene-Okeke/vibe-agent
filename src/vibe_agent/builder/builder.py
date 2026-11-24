
import subprocess
import tempfile
import zipfile
import time
import os
from vibe_agent.manifest import Manifest


# --------------build----------------------------------------------------------

def unpack_upload( path: str ) -> str:
    temporary_folder = tempfile.mkdtemp(prefix="vibe-build-")
    with zipfile.ZipFile(path)as zip_file:
        zip_file.extractall(temporary_folder)
    return temporary_folder

def find_build_folder( temporary_folder:  str, manifest: Manifest ) -> str:
    if manifest.workspace_root is not None:
        return temporary_folder+ "/" + manifest.workspace_root
    return temporary_folder + "/" + manifest.folder



def write_build_files( build_folder: str, dockerfile: str,dockerignore:str) -> None:
    with open(os.path.join(build_folder, "Dockerfile"),'w') as file:
        file.write(dockerfile) 
    with open(os.path.join(build_folder, ".dockerignore"), 'w') as file:
        file.write(dockerignore) 


def build_image(build_folder: str, tag: str, build_args: dict[str, str], timeout_seconds: int ) -> dict: 
    command = ["docker", "build", "--progress=plain", "-t", tag] + build_arg_flags(build_args) + ["."]
    

    try:
        result = subprocess.run(command,capture_output=True, text=True,cwd=build_folder, timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        return {"ok": False, "logs": "Build took longer than " + str(timeout_seconds) + " seconds"}
    
    logs  = result.stdout + result.stderr

    if result.returncode != 0:
        return {"ok": False, "logs": logs}
    return {"ok":True, "logs":logs}


BUILD_TIMEOUT_SECONDS = 600
def build(unpacked: str, manifest: Manifest, dockerfile: str, dockerignore:str, tag: str ,build_args: dict[str, str], timeout_seconds: int = BUILD_TIMEOUT_SECONDS ) -> dict:
    
    build_folder = find_build_folder(unpacked,manifest)
    write_build_files(build_folder,dockerfile, dockerignore)
    result = build_image(build_folder,tag,build_args,timeout_seconds)
    return result



#------------------run----------------------------------------------

def env_flags(runtime_env: dict[str,str]) -> list[str]:
    flags = []
    for key,value in runtime_env.items():
        flags.append("-e")
        flags.append(key+"="+value)
    return flags

def is_running(container_id: str) -> bool:
    result = subprocess.run(["docker", "inspect", "-f", "{{.State.Running}}", container_id], capture_output=True, text=True)
    return result.stdout.strip() == "true"

def container_logs(container_id: str ) -> str:
    result = subprocess.run(["docker", "logs",container_id], capture_output=True, text=True)
    return result.stdout + result.stderr

 # run starts the container and Docker picks a free port on your machine for it. 
 # find_address asks Docker which one it picked, using docker port, which prints something like 127.0.0.1:32768. 
 # run puts http:// in front, and that's the app's URL
 
def find_address(container_id: str, port: int ) -> str:
    result = subprocess.run(["docker", "port", container_id, str(port)], capture_output=True, text=True)
    lines = result.stdout.splitlines()[0]
    if not lines:
        return None
    return lines[0]

def remove_container( container_id: str ) -> None:
    subprocess.run(["docker", "rm", "-f", container_id], capture_output=True, text=True)


def run ( tag:  str, port: int, runtime_env: dict[str, str] ) -> dict:
    command = ["docker", "run", "-d", "--pull", "never", "-p", "127.0.0.1::" + str(port)] + env_flags(runtime_env) + [tag]

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        return {"ok": False, "logs": result.stderr}

    container_id = result.stdout.strip()
    time.sleep(2)

    if is_running(container_id) is False:
        logs = container_logs(container_id)
        remove_container(container_id)
        return {"ok":False,"logs":logs}

    address = find_address(container_id, port)
    if not address:
        remove_container(container_id)
        return {"ok": False, "logs": "The container is not listening on port " + str(port)}

    return{"ok": True, "container_id":container_id,"url":'http://' + address}

def build_arg_flags( build_args: dict[str, str] ) -> list[str]:
    flags = []
    for key, value in build_args.items():
        flags.append('--build-arg')
        flags.append(key + '=' + value)
    return flags



