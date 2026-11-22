from vibe_agent.manifest import Manifest
from vibe_agent.generator.planner import make_build_plan, check_llm_answers

# --- Test 1: the rules can't find the start command → the LLM fills it ---
weird_app = Manifest(
    folder="api",
    markers=["package.json"],
    marker_files={
        "package.json": '{"scripts": {"dev": "nodemon"}, "dependencies": {"express": "^4.19.0"}}'
    },
    files=["package.json", "package-lock.json", "app/main.js", "app/routes.js"],
    lockfile="package-lock.json",
)
print("TEST 1: weird Express app")
print(make_build_plan(weird_app).model_dump_json(indent=2))

# --- Test 2: a normal Vite app → rules decide everything, no LLM call ---
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
print("\nTEST 2: normal Vite app")
print(make_build_plan(vite_app).model_dump_json(indent=2))

# --- Test 3: pretend the LLM gave bad answers → the checks must reject them ---
print("\nTEST 3: bad LLM answers")
bad_answers = [
    {"start_command": "node server.js"},      # file doesn't exist
    {"start_command": "nodemon app/main.js"}, # dev command
    {},                                       # didn't answer at all
]
for bad in bad_answers:
    try:
        check_llm_answers(weird_app, bad, ["start_command"])
        print(f"  ❌ NOT caught: {bad}")
    except ValueError as error:
        print(f"  ✅ caught: {error}")