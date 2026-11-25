import tempfile
from pathlib import Path
from vibe_agent.generator.build_plan import BuildPlan
from vibe_agent.fixer.fix_suggestion import FixSuggestion, CodeEdit
from vibe_agent.fixer.apply import apply_plan_changes, apply_code_edits

# ---------- Part 1: plan fixes ----------
plan = BuildPlan(framework="vite", runtime_version="22", package_manager="npm",
                 has_lockfile=True, install_command="npm ci", build_command="npm run build",
                 start_command=None, output_dir="dist", port=80, confidence="high")

good = FixSuggestion(kind="plan", explanation="t", plan_changes={"runtime_version": "20"})
new_plan = apply_plan_changes(plan, good)
print("PLAN: runtime", plan.runtime_version, "→", new_plan.runtime_version, "| confidence:", new_plan.confidence)

bad = FixSuggestion(kind="plan", explanation="t", plan_changes={"port": 99999})
try:
    apply_plan_changes(plan, bad)
    print("❌ bad port NOT caught")
except ValueError:
    print("✅ bad port 99999 rejected by pydantic")

# ---------- Part 2: code fixes, in a throwaway folder ----------
folder = tempfile.mkdtemp()                  # a fresh empty folder, just for this test
app = Path(folder) / "src" / "App.jsx"
app.parent.mkdir()                           # make the src/ folder
app.write_text('<div className="card">\n  <p>Products</p>\n\n<div className="card">\n  <p>Orders</p>\n')

# two edits in the SAME file: close both divs
fix = FixSuggestion(kind="code", explanation="t", edits=[
    CodeEdit(file="src/App.jsx", find="  <p>Products</p>", replace="  <p>Products</p>\n</div>"),
    CodeEdit(file="src/App.jsx", find="  <p>Orders</p>",   replace="  <p>Orders</p>\n</div>"),
])
apply_code_edits(folder, fix)
print("\nAFTER BOTH EDITS:\n" + app.read_text())

# all-or-nothing: edit 1 is fine, edit 2 can't be found → NOTHING should be written
before = app.read_text()
broken = FixSuggestion(kind="code", explanation="t", edits=[
    CodeEdit(file="src/App.jsx", find="  <p>Products</p>", replace="CHANGED"),
    CodeEdit(file="src/App.jsx", find="this text does not exist", replace="x"),
])
try:
    apply_code_edits(folder, broken)
    print("❌ broken fix NOT caught")
except ValueError as error:
    print("✅ broken fix rejected:", error)
print("file untouched?", app.read_text() == before)