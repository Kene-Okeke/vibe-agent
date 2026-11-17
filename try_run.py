from vibe_agent.inspector.inspector import inspect
from vibe_agent.builder.builder import build, run, remove_container

CRASH_DOCKERFILE = """FROM caddy:2-alpine
CMD ["sh", "-c", "echo DATABASE_URL is missing; exit 1"]
"""

path = "test-zips/good.zip"
manifest = inspect(path)[0]
print("build crash:", build(path, manifest, CRASH_DOCKERFILE, "vibe-crash:1")["ok"])

tests = [
    ("site", "vibe-good:1", 80, {"GREETING": "hello"}),
    ("site again", "vibe-good:1", 80, {}),
    ("crashes on start", "vibe-crash:1", 80, {}),
    ("no such image", "vibe-nothing:1", 80, {}),
]

started = []
for label, tag, port, runtime_env in tests:
    result = run(tag, port, runtime_env)
    print(label, "-> ok:", result["ok"])
    if result["ok"]:
        print("   url:", result["url"])
        started.append(result["container_id"])
    else:
        print("   error:", result["logs"].strip().splitlines()[0])

input("Open the urls, then press Enter to stop the containers...")
for container_id in started:
    remove_container(container_id)
print("stopped", len(started))