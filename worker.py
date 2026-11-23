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
from vibe_agent.generator.planner import make_build_plan
from vibe_agent.generator.render import render_dockerfile, render_dockerignore

load_dotenv()
API_URL = os.environ["API_URL"]
WORKER_TOKEN = os.environ["WORKER_TOKEN"]

POLL_SECONDS = 5
HEARTBEAT_SECONDS = 20
MAX_LOG_CHARACTERS = 10000


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
    # 1. decide how to build it (rules, plus the LLM if something was unknown)
    try:
        plan = make_build_plan(manifest)
    except ValueError as error:
        return {
            "dockerfile": None,
            "dockerignore": None,             
            "port": None,
            "build_args": {},
            "runtime_env": {},
            "warnings": [],
            "error": str(error),
        }

       # 2. write the Dockerfile from that plan
    dockerfile = render_dockerfile(plan)

    # 3. tell the user if the LLM guessed anything
    warnings = []
    if plan.confidence != "high":
        warnings.append("Some build settings were detected by AI. Check them if the deploy fails.")

    # 4. hand everything to the builder, in the shape deploy() expects
    return {
        "dockerfile": dockerfile,
        "dockerignore": render_dockerignore(),  
        "port": plan.port,
        "build_args": {},
        "runtime_env": {},
        "warnings": warnings,
        "error": None,
    }



def claim(worker_id: str ) -> dict | None:
    status, job= post("/internal/jobs/claim",{"worker_id": worker_id})
    if status == 200:
        return job
    if status != 204:
        print(worker_id, "claim failed:", status)

def finish(worker_id: str, job_id: int, outcome: dict) -> None:
    body = {
        "worker_id":worker_id, "success" : outcome['success'], "url": outcome["url"], "logs": outcome["logs"][-MAX_LOG_CHARACTERS:]
    }
    status, result = post("/internal/jobs/" + str(job_id)+"/finish",body)
    print(worker_id, "finished job", job_id, "->", status, result)

def deploy(job: dict ) -> bool:
    path = job["source_path"]

    try: 
        manifests = inspect(path)
    except ValueError as error:
        print("inspect failed:", error) 
        return {"success": False, "url": None, "logs": "inspect failed: " + str(error)}
    manifest = manifests[0]
    print("app:", manifest.folder, manifest.app_type)

    plan = generate(manifest)
    if plan["error"] is not None:
        print("no Dockerfile:", plan["error"]) 
        return {"success": False, "url": None, "logs": "no Dockerfile: " + plan["error"]}

    tag = "deployment-" + str(job["deployment_id"])
    result = build(path, manifest, plan["dockerfile"], tag, plan["build_args"])
    if not result["ok"]:
        print(" build failed:", result["logs"].splitlines()[-1]) 
        return {"success": False, "url": None, "logs": result["logs"]}

    started = run(tag, plan["port"], plan["runtime_env"])
    if not started["ok"]:
        print(" run failed:", started["logs"].splitlines()[0])
        return {"success": False, "url": None, "logs": result["logs"] + started["logs"]}

    print("   live at", started["url"])
    return {"success": True,  "url": started["url"], "logs": result["logs"]}

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
        try:
            outcome = deploy(job)
        except Exception as error:
            outcome = {"success": False, "url": None, "logs": "worker error: " + str(error)}

        stop_heartbeat.set()
        finish(worker_id, job["job_id"], outcome)

if __name__ == "__main__":
    main()