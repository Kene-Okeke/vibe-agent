from vibe_agent.manifest import Manifest
import json
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from vibe_agent.manifest import Manifest

load_dotenv()   # read .env so os.getenv can find GEMINI_API_KEY

MODEL = "gemini-3.6-flash"

# what each field means, so the LLM knows exactly what we want back
FIELD_HELP = {
    "framework": 'one of "next", "vite", "node-server", "fastapi", "static"',
    "install_command": "the production install command, e.g. npm ci",
    "build_command": "the build command, or null if there is none",
    "start_command": "the PRODUCTION start command (never nodemon, --watch, --reload or next dev), or null for vite/static",
    "port": "the port the app listens on, as a number",
    "runtime_version": 'the Node or Python version, e.g. "22" or "3.12"',
}

def build_llm_prompt(manifest:Manifest,answers:dict, unknowns: list[str]) -> str:
    #A. the evidence: the marker files the insector sent (package.json, requirements.txt ..)
    evidence = ""
    for name, text in manifest.marker_files.items():
        evidence += f"--- {name} ---\n{text}\n\n"

    # B. what the rules already decided (the LLM must not change these)
    known = ""
    for name, value in answers.items():
        if name not in unknowns:
            #json.dumps is the translator from Python to JSON
            # referring to the case of fallback , the prompt now shows build_command: null instead of none
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

def ask_llm(prompt:str) -> dict:
    # connect to Gemini with the key from .env
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    # send the prompt, wait for the reply
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",   # reply must be JSON
            temperature=0,   # no creativity: same input, same answer
        ),
    )
    # turn the reply text into a Python dict
    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        return {}

