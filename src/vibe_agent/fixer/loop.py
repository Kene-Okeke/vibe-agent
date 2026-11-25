from pathlib import Path
from vibe_agent.builder.builder import build_image
from vibe_agent.generator.build_plan import BuildPlan
from vibe_agent.generator.render import render_dockerfile, render_dockerignore
from vibe_agent.fixer.logs import trim_log
from vibe_agent.fixer.files import pick_relevant_files
from vibe_agent.fixer.prompt import build_fix_prompt
from vibe_agent.fixer.suggest import suggest_fix
from vibe_agent.fixer.check import check_fix
from vibe_agent.fixer.apply import apply_plan_changes, apply_code_edits

MAX_ATTEMPTS = 3
BUILD_TIMEOUT_SECONDS = 600


def write_build_files(folder: str, plan: BuildPlan) -> None:
    # (re)write the Dockerfile and .dockerignore from the CURRENT plan
    (Path(folder) / "Dockerfile").write_text(render_dockerfile(plan))
    (Path(folder) / ".dockerignore").write_text(render_dockerignore())


def read_files(folder: str, paths: list[str]) -> dict[str, str]:
    # turn a list of file paths into {path: the file's text}
    contents = {}
    for path in paths:
        contents[path] = (Path(folder) / path).read_text()
    return contents

def fix_and_rebuild(folder: str, plan: BuildPlan, files: list[str], tag: str, approve) -> dict:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"\n--- attempt {attempt} ---")

        # 1. build from the CURRENT plan
        write_build_files(folder, plan)
        result = build_image(folder, tag, {}, BUILD_TIMEOUT_SECONDS)
        if result["ok"]:
            return {"ok": True, "plan": plan, "attempts": attempt}

        # 2. it failed: ask the LLM what went wrong, and check its answer
        trimmed = trim_log(result["logs"])
        picked = pick_relevant_files(trimmed, files)
        contents = read_files(folder, picked)
        prompt = build_fix_prompt("build", trimmed, plan, files, contents)
        try:
            fix = suggest_fix(prompt)
            check_fix(fix, files, contents)
        except Exception as error:
            return {"ok": False, "reason": f"Couldn't get a safe fix: {error}", "log": trimmed}

        print("Diagnosis:", fix.explanation)

        # 3. act on the kind of problem
        if fix.kind == "plan":
            # our own settings were wrong: fix the plan automatically
            try:
                plan = apply_plan_changes(plan, fix)
            except ValueError as error:
                return {"ok": False, "reason": f"Bad plan fix: {error}", "fix": fix}
        elif fix.kind == "code" and fix.edits:
            # the user's code: only with their OK
            if not approve(fix):
                return {"ok": False, "reason": "User declined the fix", "fix": fix}
            apply_code_edits(folder, fix)
        else:
            # config / runtime / no edits: we can't fix this ourselves
            return {"ok": False, "reason": "Needs your action", "fix": fix}

    return {"ok": False, "reason": f"Still failing after {MAX_ATTEMPTS} attempts"}