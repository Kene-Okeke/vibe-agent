from vibe_agent.manifest import Manifest
from vibe_agent.generator.planner import make_build_plan
from vibe_agent.generator.render import render_dockerfile

flask_api = Manifest(
    folder="apps/api",
    markers=["requirements.txt"],
    marker_files={"requirements.txt": "flask==3.0.3\nrequests==2.32.3\n"},
    files=["requirements.txt", "app.py"],
    app_type="python",
)

plan = make_build_plan(flask_api)
print(plan.model_dump_json(indent=2))
print()
print(render_dockerfile(plan))