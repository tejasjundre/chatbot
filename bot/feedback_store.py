"""File-based feedback persistence for product analytics."""

from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any

_LOCK = Lock()


def append_feedback(entry: dict[str, Any], file_path: str) -> None:
    """Append one feedback record to a JSONL file."""

    path = Path(file_path)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[1] / path
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(entry, ensure_ascii=True)
    with _LOCK:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")


def count_feedback(file_path: str) -> int:
    """Return number of feedback records currently stored."""

    path = Path(file_path)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[1] / path
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for _ in handle)

