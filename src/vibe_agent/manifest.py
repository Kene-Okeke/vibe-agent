from typing import Literal
from pydantic import BaseModel


class Manifest(BaseModel):
    """
    Manifest model for the Vibe Agent.
    """
    folder: str

    #evidence - (regular app)
    markers: list[str]
    marker_files: dict[str, str]
    files: list[str]
    lockfile: str | None = None 

    # monorepo only ( Returns none for normal apps)
    workspace_root: str | None = None
    shared_packages: list[str] = []

    # hints (inferred by the inspector; None = not sure, planner verifies)
    app_type: Literal["node", "python", "static"] | None = None
    package_manager: Literal["npm", "pnpm", "yarn", "bun", "pip", "uv", "poetry"] | None = None
    role: Literal["frontend", "backend", "fullstack"] | None = None
    start_command: str | None = None

