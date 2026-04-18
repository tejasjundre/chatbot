"""Shared cached JSON data access for Plexi Bot features."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "data"


@lru_cache(maxsize=16)
def _read_json(file_name: str) -> Any:
    """Read and cache a JSON file from the project's data directory."""

    file_path = DATA_DIR / file_name
    with file_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def get_products() -> list[dict[str, Any]]:
    """Return cached product catalog data."""

    return list(_read_json("products.json"))


def get_orders() -> list[dict[str, Any]]:
    """Return cached order data."""

    return list(_read_json("orders.json"))


def get_return_policy_payload() -> dict[str, Any]:
    """Return cached return policy payload."""

    data = _read_json("return_policy.json")
    return dict(data)


def clear_data_cache() -> None:
    """Clear cached JSON content (useful for tests or hot-reload workflows)."""

    _read_json.cache_clear()

