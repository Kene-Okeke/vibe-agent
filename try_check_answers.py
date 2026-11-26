from vibe_agent.manifest import Manifest
from vibe_agent.generator.planner import check_llm_answers

app = Manifest(
    folder="api",
    markers=["package.json"],
    marker_files={"package.json": '{"dependencies": {"express": "^4.19.0"}}'},
    files=["package.json", "app/main.js"],
)

# TWO unknowns: this is the case the indentation bug broke
answers = {"start_command": "node app/main.js", "port": 3000}
print("two unknowns:", check_llm_answers(app, answers, ["start_command", "port"]))

# bad answers must still be rejected
bad_answers = [
    {"start_command": "node server.js"},       # file doesn't exist
    {"start_command": "nodemon app/main.js"},  # dev command
    {},                                        # didn't answer
]
for bad in bad_answers:
    try:
        check_llm_answers(app, bad, ["start_command"])
        print("❌ NOT caught:", bad)
    except ValueError as error:
        print("✅ caught:", error)