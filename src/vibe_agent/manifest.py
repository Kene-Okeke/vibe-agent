from typing import Literal
from pydantic import BaseModel


class Manifest(BaseModel):
    """
    Manifest model for the Vibe Agent.
    """
    folder: str
    markers: list[str]
    marker_files: dict[str, str]
    files: list[str]
    app_type: Literal["node", "python", "static"] | None = None
    role: Literal["frontend", "backend", "fullstack"] | None = None
    start_command: str | None = None

