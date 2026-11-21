from vibe_agent.manifest import Manifest
from vibe_agent.generator.llm_fallback import build_llm_prompt
from vibe_agent.generator.llm_fallback import ask_llm

# an Express app the rules CAN'T fully figure out:
# no "start" script, and the entry file isn't one of our usual names
weird_app = Manifest(
    folder="api",
    markers=["package.json"],
    marker_files={
        "package.json": '{"scripts": {"dev": "nodemon"}, "dependencies": {"express": "^4.19.0"}}'
    },
    files=["package.json", "package-lock.json", "app/main.js", "app/routes.js"],
    lockfile="package-lock.json",
)

# what the planner's detectors would return for it (written by hand for this test)
answers = {
    "framework": "node-server",
    "install_command": "npm ci",
    "build_command": None,
    "start_command": "unknown",
    "port": 3000,
    "runtime_version": "22",
}
unknowns = ["start_command"]

print(build_llm_prompt(weird_app, answers, unknowns))
print(ask_llm(build_llm_prompt(weird_app, answers, unknowns)))