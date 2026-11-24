from vibe_agent.generator.build_plan import BuildPlan

# how to classify the failure: matches FixSuggestion.kind
KIND_HELP = """- "plan": OUR build settings were wrong (Node/Python version, install/build/start command, port). Use plan_changes.
- "config": a required environment variable or secret is missing. List the names in missing_env.
- "code": a bug in the app's own code (wrong import path, package missing from package.json). Use edits.
- "runtime": it built but crashed on start for another reason. Explain it; add edits only if a small change clearly fixes it."""

# the exact JSON shape we want back: KEEP IN SYNC with the FixSuggestion model
REPLY_SHAPE = """{
  "kind": "plan" | "config" | "code" | "runtime",
  "explanation": "plain English for a non-technical person, 1-3 sentences",
  "edits": [{"file": "path/in/project", "find": "exact text currently in the file", "replace": "the new text"}],
  "plan_changes": {"build_plan_field": "new value"},
  "missing_env": ["VARIABLE_NAME"]
}"""

def build_fix_prompt(stage: str, log: str, plan: BuildPlan,files: list[str], file_contents: dict[str, str]) -> str:
    # the relevant files' contents, each labelled with its name
    sources = ""
    for name, text in file_contents.items():
         sources += f"--- {name} ---\n{text}\n\n"

    return f"""You are helping fix a failed deploy of a user's app with Docker.

    The deploy failed during: {stage}

Our build plan (we generated this, it may be wrong):
{plan.model_dump_json(indent=2)}

Files in the project:
{files}

Contents of the relevant files:
{sources}
Log (trimmed):
{log}

Classify the failure as exactly ONE kind:
{KIND_HELP}

Rules:
- Only edit files whose contents are shown above. Never edit .env files, lockfiles or secrets.
- "find" must be copied EXACTLY from the file shown, character for character.
- Keep edits small. If you are not sure of a fix, explain the problem and leave edits empty.

Reply with ONLY a JSON object in this shape. No markdown:
{REPLY_SHAPE}"""
