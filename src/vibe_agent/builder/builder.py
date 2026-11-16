import shutil
import subprocess
import tempfile
import zipfile

from vibe_agent.manifest import Manifest

def unpack_upload( path: str ) -> str:
    temporary_folder = tempfile.mkdtemp(prefix="vibe-build-")
    with zipfile.ZipFile(path)as zip_file:
        zip_file.extractall(temporary_folder)
    return temporary_folder

def find_build_folder( temporary_folder:  str, manifest: Manifest ) -> str:
    if manifest.workspace_root is not None:
        return temporary_folder+ "/" + manifest.workspace_root
    return temporary_folder + "/" + manifest.folder


DOCKERIGNORE = "node_modules\ndist\n.git\n.env*\nDockerfile\n.dockerignore\n"
def write_build_files( build_folder: str, dockerfile: str ) -> None:
    with open(build_folder + "Dockerfile", 'w') as file:
        file.write(dockerfile) 
    with open(build_folder + ".dockerignore", 'w') as file:
        file.write(DOCKERIGNORE) 


def build_image(build_folder: str, tag: str ) -> dict:
    result = subprocess.run(["docker", "build", "--progress=plain", "-t", tag, "."],cwd=build_folder, capture_output=True, text=True)
    logs  = result.stdout + result.stderr

    if result.returncode is not 0:
        return {"ok": False, "logs": logs}
    return {"ok":True, "logs":logs}

def build( path: str, manifest: Manifest, dockerfile: str, tag: str ) -> dict:
    unpacked = unpack_upload(path)
    build_folder = find_build_folder(unpacked,manifest)
    write_build_files(build_folder,dockerfile)
    result = build_image(build_folder,tag)
    shutil.rmtree(unpacked) 




