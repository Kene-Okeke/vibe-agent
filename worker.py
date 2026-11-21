import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request

from dotenv import load_dotenv

from vibe_agent.builder.builder import build, run
from vibe_agent.inspector.inspector import inspect
from vibe_agent.manifest import Manifest

load_dotenv()
API_URL = os.environ["API_URL"]
WORKER_TOKEN = os.environ["WORKER_TOKEN"]

POLL_SECONDS = 5
HEARTBEAT_SECONDS = 20


def post(path: str, body: dict) -> tuple[int, dict | None]:
    request = urllib.request.Request(
        API_URL + path,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + WORKER_TOKEN},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request) as response:
            text = response.read()
            if text:
                return response.status, json.loads(text)
            return response.status, None
    except urllib.error.HTTPError as error:
        return error.code, None


def keep_alive(worker_id: str, job_id: int) -> threading.Event:
    stop = threading.Event()

    def beat():
        while not stop.wait(HEARTBEAT_SECONDS):
            status, body = post("/internal/jobs/" + str(job_id) + "/heartbeat", {"worker_id": worker_id})
            if status != 200:
                print(worker_id, "heartbeat failed for job", job_id, "->", status)

    threading.Thread(target=beat, daemon=True).start()
    return stop


def generate(manifest: Manifest) -> dict:
    # Okeke's generator (planner + render) plugs in here.
    return {"dockerfile": None, "port": None, "build_args": {}, "runtime_env": {},
            "warnings": [], "error": "Dockerfile generator not connected yet"}


def claim(worker_id: str ) -> dict | None:
    status, job= post("/internal/jobs/claim",{"worker_id": worker_id})
    if status == 200:
        return job
    if status != 204:
        print(worker_id, "claim failed:", status)

def finish(worker_id: str, job_id: int, success: bool) -> None:
    status, result = post("/internal/jobs/" + str(job_id)+"/finish",{"worker_id": worker_id, "success": success})
    print(worker_id, "finished job", job_id, "->", status, result)

def deploy(job: dict ) -> bool:
    path = job["source_path"]

    try: 
        manifests = inspect(path)
    except ValueError as error:
        print("inspect failed:", error) 
        return False
    manifest = manifests[0]
    print("app:", manifest.folder, manifest.app_type)

    plan = generate(manifest)
    if plan["error"] is not None:
        print("no Dockerfile:", plan["error"]) 
        return False

    tag = "deployment-" + str(job["deployment_id"])
    result = build(path, manifest, plan["dockerfile"], tag, plan["build_args"])
    if not result["ok"]:
        print(" build failed:", result["logs"].splitlines()[-1]) 
        return False

    started = run(tag, plan["port"], plan["runtime_env"])
    if not started["ok"]:
        print(" run failed:", started["logs"].splitlines()[0])
        return False

    print("   live at", started["url"])
    return True

def main() -> None:
    worker_id = sys.argv[1]
    print(worker_id, "started")
    while True:
        job= claim(worker_id)
        if job is None:
            time.sleep(POLL_SECONDS)
            continue
        print(worker_id, "got job", job["job_id"], "for", job["source_path"])
        stop_heartbeat = keep_alive(worker_id, job["job_id"])
        success = deploy(job)
        stop_heartbeat.set()
        finish(worker_id, job["job_id"], success)

main()