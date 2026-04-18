"""Runtime settings loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


def _to_bool(value: str | None, default: bool = False) -> bool:
    """Convert an environment value to bool with a default fallback."""

    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _to_int(value: str | None, default: int) -> int:
    """Convert an environment value to int with a default fallback."""

    try:
        return int(value) if value is not None else default
    except ValueError:
        return default


def _parse_origins(raw: str | None) -> list[str]:
    """Parse comma-separated CORS origins."""

    if not raw:
        return ["*"]
    values = [item.strip() for item in raw.split(",")]
    return [item for item in values if item] or ["*"]


@dataclass(frozen=True)
class Settings:
    """Immutable application settings object."""

    app_env: str
    app_api_key: str
    cors_origins: list[str]
    chat_rate_limit_per_minute: int
    enable_metrics: bool
    feedback_log_path: str

    @property
    def auth_required(self) -> bool:
        """Return True when API auth is enabled."""

        return bool(self.app_api_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and cache process-level settings."""

    return Settings(
        app_env=os.getenv("APP_ENV", "development").strip().lower(),
        app_api_key=os.getenv("APP_API_KEY", "").strip(),
        cors_origins=_parse_origins(os.getenv("CORS_ORIGINS", "*")),
        chat_rate_limit_per_minute=max(
            1, _to_int(os.getenv("CHAT_RATE_LIMIT_PER_MINUTE"), 30)
        ),
        enable_metrics=_to_bool(os.getenv("ENABLE_METRICS"), True),
        feedback_log_path=os.getenv("FEEDBACK_LOG_PATH", "data/feedback_log.jsonl"),
    )

