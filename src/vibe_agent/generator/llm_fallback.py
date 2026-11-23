import json
from vibe_agent.manifest import Manifest

# what each field means, so the LLM knows exactly what we want back
FIELD_HELP = {
    "framework": 'one of "next", "vite", "node-server", "fastapi", "static"',
    "install_command": "the production install command, e.g. npm ci",
    "build_command": "the build command, or null if there is none",
    "start_command": "the PRODUCTION start command (never nodemon, --watch, --reload or next dev), or null for vite/static",
    "port": "the port the app listens on, as a number",
    "runtime_version": 'the Node or Python version, e.g. "22" or "3.12"',
}


def build_llm_prompt(manifest: Manifest, answers: dict, unknowns: list[str]) -> str:
    # A. the evidence: the marker files the inspector sent (package.json, requirements.txt, ...)
    evidence = ""
    for name, text in manifest.marker_files.items():
        evidence += f"--- {name} ---\n{text}\n\n"

    # B. what the rules already decided (the LLM must not change these)
    known = ""
    for name, value in answers.items():
        if name not in unknowns:
            # json.dumps translates Python to JSON, so None shows as null
            known += f"{name}: {json.dumps(value)}\n"

    # C. only the fields we need the LLM to fill in, each with its rules
    wanted = ""
    for name in unknowns:
        wanted += f'"{name}": {FIELD_HELP[name]}\n'

    # D. the full question
    return f"""You are helping deploy an app with Docker.

Files in the project:
{manifest.files}

Contents of key files:
{evidence}
Already decided (do not change):
{known}
Fill in ONLY these fields:
{wanted}
Reply with ONLY a JSON object with exactly these keys. No explanation, no markdown."""