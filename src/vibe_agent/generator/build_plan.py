from typing import Literal
from pydantic import BaseModel, Field


class BuildPlan(BaseModel):
    framework: Literal["next", "vite", "node-server", "fastapi", "static"]
    runtime_version:str
    package_manager: Literal["npm","pnpm","yarn", "pip","uv","bun", "poetry"]| None = None 
        # none below means this is a static site, so no package manager is needed
    has_lockfile: bool=False
        # if has_lockfile is True → npm ci (exact versions)
        # if False → npm install (using e.g package,json), plus a warning: “no lockfile, versions may differ”
    install_command: str | None = None
    build_command: str | None = None
    start_command: str | None = None
    output_dir: str | None = None 
    port: int = Field(ge=1, le=65535)
    confidence: Literal["high", "medium", "low"] 



