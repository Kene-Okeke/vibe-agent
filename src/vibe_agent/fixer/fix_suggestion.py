from typing import Literal
from pydantic import BaseModel

class CodeEdit(BaseModel):
    """One exact change to one file: find this text, replace it with that."""
    file: str
    find: str
    replace: str

class FixSuggestion(BaseModel):
    """The LLM's diagnosis of a failed deploy, and what to do about it."""
    kind: Literal["plan", "config", "code", "runtime"]
    explanation: str
    edits: list[CodeEdit] = []
    plan_changes: dict[str, str | int | None] = {}
    missing_env: list[str] = []
