from pathlib import Path
from vibe_agent.manifest import Manifest
from vibe_agent.generator.planner import make_build_plan
from vibe_agent.generator.render import render_dockerfile, render_dockerignore

# where the test app lives
app = Path.home() / "Desktop" / "vibe-test-app"

# build a Manifest by hand, the way the inspector would, using the REAL file contents
manifest = Manifest(
    folder=".",
    markers=["package.json"],
    marker_files={
        "package.json": (app / "package.json").read_text(),
        "vite.config.js": (app / "vite.config.js").read_text(),
    },
    files=["package.json", "package-lock.json", "index.html", "vite.config.js"],
    lockfile="package-lock.json",
    app_type="node",
)

# your planner + render
plan = make_build_plan(manifest)
print(plan.model_dump_json(indent=2))

# write the files INTO the test app's folder
(app / "Dockerfile").write_text(render_dockerfile(plan))
(app / ".dockerignore").write_text(render_dockerignore())
print("wrote Dockerfile and .dockerignore into", app)