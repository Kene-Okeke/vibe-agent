from vibe_agent.inspector.inspector import inspect
from vibe_agent.builder.builder import build

STATIC_DOCKERFILE = """FROM caddy:2-alpine
COPY . /usr/share/caddy
EXPOSE 80
"""

VITE_DOCKERFILE = """FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM caddy:2-alpine
COPY --from=build /app/dist /usr/share/caddy
EXPOSE 80
"""

BROKEN_DOCKERFILE = """FROM caddy:2-alpine
COPY missing.txt /usr/share/caddy
"""

tests = [
    ("good.zip", STATIC_DOCKERFILE, "vibe-good:1"),
    ("hello.zip", VITE_DOCKERFILE, "vibe-hello:1"),
    ("good.zip", BROKEN_DOCKERFILE, "vibe-broken:1"),
]

for name, dockerfile, tag in tests:
    path = "test-zips/" + name
    manifest = inspect(path)[0]
    result = build(path, manifest, dockerfile, tag)
    print(name, "->", tag, "| ok:", result["ok"])
    if not result["ok"]:
        print("   error:", result["logs"].splitlines()[-1])