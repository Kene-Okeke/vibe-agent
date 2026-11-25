from pathlib import Path
from vibe_agent.generator.build_plan import BuildPlan
from vibe_agent.fixer.fix_suggestion import FixSuggestion


def apply_plan_changes(plan: BuildPlan, fix: FixSuggestion) -> BuildPlan:
    # the current plan as a dict, with the fix's changes pasted over it
    updated = plan.model_dump() | fix.plan_changes

    # the AI changed our plan, so we're no longer fully sure
    updated["confidence"] = "medium"

    # build a NEW plan: pydantic re-checks every value
    return BuildPlan.model_validate(updated)


def apply_code_edits(source_folder: str, fix: FixSuggestion) -> None:
    # 1. work out every file's new text IN MEMORY first
    new_texts = {}
    for edit in fix.edits:
        path = Path(source_folder) / edit.file
        text = new_texts.get(edit.file, path.read_text())

        if text.count(edit.find) != 1:
            raise ValueError(f"'find' no longer matches exactly once in {edit.file}")

        new_texts[edit.file] = text.replace(edit.find, edit.replace, 1)

    # 2. only if EVERY edit worked, write the files to disk
    for file, text in new_texts.items():                     
        (Path(source_folder) / file).write_text(text)