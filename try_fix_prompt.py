from vibe_agent.generator.build_plan import BuildPlan
from vibe_agent.fixer.logs import trim_log
from vibe_agent.fixer.files import pick_relevant_files
from vibe_agent.fixer.prompt import build_fix_prompt

# the plan we made for this app (the one from your real Vite test)
plan = BuildPlan(
    framework="vite", runtime_version="22", package_manager="npm",
    has_lockfile=True, install_command="npm ci", build_command="npm run build",
    start_command=None, output_dir="dist", port=80, confidence="high",
)

# every file in the project (note: header.tsx is lowercase!)
files = ["package.json", "package-lock.json", "index.html", "src/App.tsx", "src/header.tsx", "src/main.tsx", ".env"]

# a failed build log
log = """#9 [build 5/5] RUN npm run build
#9 2.31 src/App.tsx(3,20): error TS2307: Cannot find module './Header' or its corresponding type declarations.
#9 ERROR: process "/bin/sh -c npm run build" did not complete successfully: exit code: 2"""

# 1. trim the log, 2. pick the files
trimmed = trim_log(log)
picked = pick_relevant_files(trimmed, files)
print("PICKED FILES:", picked)

# 3. pretend we read them from the unpacked folder (C6 will do this for real)
file_contents = {
    "src/App.tsx": "import Header from './Header'\n\nexport default function App() {\n  return <Header />\n}\n",
    "package.json": '{"name": "shop", "scripts": {"build": "vite build"}, "devDependencies": {"vite": "^5.0.0"}}',
}

# 4. build the prompt
prompt = build_fix_prompt("build", trimmed, plan, files, file_contents)
print("\n----- PROMPT -----\n")
print(prompt)

from vibe_agent.fixer.suggest import suggest_fix

fix = suggest_fix(prompt)
print("\n----- GEMINI'S FIX -----\n")
print(fix.model_dump_json(indent=2))