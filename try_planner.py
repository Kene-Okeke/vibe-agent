from vibe_agent.manifest import Manifest
from vibe_agent.generator.planner import make_build_plan

vite_app = Manifest(
    folder="frontend",
    markers=["package.json"],
    marker_files={
        "package.json": '{"scripts": {"build": "vite build"}, "devDependencies": {"vite": "^5.0.0"}}'
    },
    files=["package.json", "index.html", "src/main.js"],
    lockfile="package-lock.json",
    app_type="node",
)

plan = make_build_plan(vite_app)
print(plan.model_dump_json(indent=2))

from vibe_agent.generator.render import render_dockerfile

print(render_dockerfile(plan))

from vibe_agent.generator.render import render_dockerignore

print(render_dockerignore())