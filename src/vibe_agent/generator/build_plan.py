from typing import Literal
from pydantic import BaseModel, Field


class BuildPlan(BaseModel):
    """
    The generator's decision on how to build one service.
    """
    framework: Literal["next", "vite", "node-server", "fastapi", "flask", "static"]
    runtime_version: str | None = None
    package_manager: Literal["npm", "pnpm", "yarn", "bun", "pip", "uv", "poetry"] | None = None
    has_lockfile: bool = False
    install_command: str | None = None
    build_command: str | None = None
    start_command: str | None = None
    output_dir: str | None = None
    port: int = Field(ge=1, le=65535)
    confidence: Literal["high", "medium", "low"]