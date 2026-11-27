import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
import shutil

from dotenv import load_dotenv

from vibe_agent.builder.builder import build, run,unpack_upload
from vibe_agent.inspector.inspector import inspect
from vibe_agent.manifest import Manifest
from vibe_agent.generator.planner import make_build_plan
from vibe_agent.generator.render import render_dockerfile, render_dockerignore
from vibe_agent.fixer.loop import fix_and_rebuild
from vibe_agent.builder.builder import find_build_folder

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
        "worker_id": worker_id,
        "success": outcome["success"],
        "url": outcome["url"],
        "logs": outcome["logs"][-MAX_LOG_CHARACTERS:],
        "services": [],
    }
    for service in outcome["services"]:
        body["services"].append({
            "folder": service["folder"],
            "success": service["success"],
            "url": service["url"],
            "logs": service["logs"][-MAX_LOG_CHARACTERS:],
        })
    status, result = post("/internal/jobs/" + str(job_id) + "/finish", body)
    print(worker_id, "finished job", job_id, "->", status, result)

def first_line(text: str) -> str:
    lines = text.strip().splitlines()
    if not lines:
        return "(no output)"
    return lines[0]


def last_line(text: str) -> str:
    lines = text.strip().splitlines()
    if not lines:
        return "(no output)"
    return lines[-1]


def deploy_one_app(unpacked: str, manifest: Manifest, tag: str) -> dict:
    plan = generate(manifest)
    if plan["error"] is not None:
        print("   no Dockerfile:", plan["error"])
        return {"folder": manifest.folder, "success": False, "url": None, "logs": "no Dockerfile: " + plan["error"]}

    result = build(unpacked, manifest, plan["dockerfile"], plan["dockerignore"], tag, plan["build_args"])
    if not result["ok"]:
        print("   build failed:", last_line(result["logs"]))
        return {"folder": manifest.folder, "success": False, "url": None, "logs": result["logs"]}

    run_result = run(tag, plan["port"], plan["runtime_env"])
    if not run_result["ok"]:
        print("   run failed:", first_line(run_result["logs"]))
        return {"folder": manifest.folder, "success": False, "url": None, "logs": result["logs"] + run_result["logs"]}

    print("   live at", run_result["url"])
    return {"folder": manifest.folder, "success": True, "url": run_result["url"], "logs": result["logs"]}


def deploy_job(job: dict) -> dict:
    path = job["source_path"]
    try:
        manifests = inspect(path)
    except ValueError as error:
        print("   inspect failed:", error)
        return {"success": False, "url": None, "logs": "inspect failed: " + str(error), "services": []}

    services = []
    unpacked = unpack_upload(path)
    try:
        for number, manifest in enumerate(manifests, start=1):
            print("   app", number, "of", len(manifests), ":", manifest.folder, manifest.app_type)
            tag = "deployment-" + str(job["deployment_id"]) + "-" + str(number)
            services.append(deploy_one_app(unpacked, manifest, tag))
    finally:
        shutil.rmtree(unpacked)

    success = True
    url = None
    logs = ""
    for service in services:
        if not service["success"]:
            success = False
        if url is None:
            url = service["url"]
        logs = logs + "== " + service["folder"] + " ==\n" + service["logs"] + "\n"
    return {"success": success, "url": url, "logs": logs, "services": services}


def main() -> None:
    worker_id = sys.argv[1]
    print(worker_id, "started")
    while True:
        job = claim(worker_id)
        if job is None:
            time.sleep(POLL_SECONDS)
            continue
        print(worker_id, "got job", job["job_id"], "for", job["source_path"])
        stop_heartbeat = keep_alive(worker_id, job["job_id"])
        try:
            outcome = deploy_job(job)
        except Exception as error:
            outcome = {"success": False, "url": None, "logs": "worker error: " + str(error), "services": []}

        stop_heartbeat.set()
        finish(worker_id, job["job_id"], outcome)


if __name__ == "__main__":
    main()