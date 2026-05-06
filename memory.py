import json
import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Literal

from pydantic import BaseModel, Field


class Lesson(BaseModel):
    """Structured lesson extracted after a solve."""

    condition: str
    action: str
    rationale: str
    generality: Literal["problem_specific", "family_specific", "domain_general"]


class MemoryEntry(BaseModel):
    """Persistent memory entry stored after each solve."""

    entry_id: str = Field(description="Unique entry identifier")
    source_problem_id: str = Field(description="Problem id that produced the lesson")
    problem_features: str = Field(
        description="Short description of problem features for retrieval"
    )
    outcome: Literal["pass", "fail"]
    failure_type: Optional[str] = None
    lesson: Lesson
    timestamp: str


def generate_entry_id() -> str:
    return str(uuid.uuid4())


def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


class MemoryStore:
    """Simple JSON-backed memory store."""

    def __init__(self, path: str = "memory_dump.json") -> None:
        self.path = path

    def _load_raw(self) -> List[dict]:
        if not os.path.exists(self.path):
            return []
        with open(self.path, "r") as f:
            return json.load(f)

    def _save_raw(self, items: List[dict]) -> None:
        with open(self.path, "w") as f:
            json.dump(items, f, indent=2)

    def read_all(self) -> List[MemoryEntry]:
        return [MemoryEntry(**item) for item in self._load_raw()]

    def read_by_id(self, entry_id: str) -> Optional[MemoryEntry]:
        for item in self._load_raw():
            if item.get("entry_id") == entry_id:
                return MemoryEntry(**item)
        return None

    def write(self, entry: MemoryEntry) -> None:
        items = self._load_raw()
        items.append(entry.model_dump())
        self._save_raw(items)

    def reset(self) -> None:
        self._save_raw([])
