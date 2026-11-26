from vibe_agent.manifest import Manifest
from vibe_agent.generator.planner import make_build_plan
from vibe_agent.generator.render import render_dockerfile

# the app inside the monorepo, as the inspector would describe it
web_app = Manifest(
    folder="apps/web",
    workspace_root=".",
    markers=["package.json"],
    marker_files={
        "package.json": '{"name": "web", "scripts": {"build": "vite build"}, "devDependencies": {"vite": "^5.0.0"}}'
    },
    files=["package.json", "index.html", "src/main.jsx"],
    lockfile="package-lock.json",
    app_type="node",
)

plan = make_build_plan(web_app)
print("build_command:", plan.build_command)
print("output_dir:   ", plan.output_dir)
print()
print(render_dockerfile(plan))