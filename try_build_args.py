import subprocess
from vibe_agent.inspector.inspector import inspect
from vibe_agent.builder.builder import build

ARGS_DOCKERFILE = """FROM caddy:2-alpine
ARG GREETING
RUN echo "$GREETING" > /usr/share/caddy/greeting.txt
"""

SLOW_DOCKERFILE = """FROM caddy:2-alpine
RUN sleep 30
"""

path = "test-zips/good.zip"
manifest = inspect(path)[0]

result = build(path, manifest, ARGS_DOCKERFILE, "vibe-args:1", {"GREETING": "hello from a build arg"})
print("build args -> ok:", result["ok"])
inside = subprocess.run(["docker", "run", "--rm", "vibe-args:1", "cat", "/usr/share/caddy/greeting.txt"],
                        capture_output=True, text=True)
print("   greeting.txt:", inside.stdout.strip())

result = build(path, manifest, SLOW_DOCKERFILE, "vibe-slow:1", {}, timeout_seconds=5)
print("slow build -> ok:", result["ok"])
print("   error:", result["logs"])