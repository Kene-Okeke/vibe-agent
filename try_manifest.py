from vibe_agent.manifest import Manifest

# A valid manifest: what the inspector would send for a Python backend
good = {
    "folder": "my-app/backend/",
    "markers": ["requirements.txt"],
    "marker_files": {"requirements.txt": "fastapi\nuvicorn\n"},
    "files": ["app/main.py", "app/tables.py"],
    "app_type": "python",
    "role": "backend",
    "start_command": "uvicorn app.main:app",
}

manifest = Manifest.model_validate(good)
print("VALID:", manifest)
print("app_type is:", manifest.app_type)

# A broken manifest: same as above, but with one mistake
bad = dict(good)          # copy the good one
bad["app_type"] = "django"   # not one of "node", "python", "static"

Manifest.model_validate(bad)   # this line should crash