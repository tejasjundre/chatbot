"""Phase 1: Return policy Q&A feature."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from bot.conversation import Message
from bot.data_store import get_return_policy_payload
from bot.llm import LLMServiceError, call_claude
from bot.prompts import build_return_policy_prompt

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "return_policy.json"
LLMCallable = Callable[[str, list[Message], str], str]


def load_return_policy(path: Path = DATA_FILE) -> str:
    """Load return policy text from JSON data."""

    if path == DATA_FILE:
        data = get_return_policy_payload()
    else:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    policy = data.get("policy", "")
    if isinstance(policy, list):
        return "\n".join(policy)
    return str(policy)


def answer_return_policy_question(
    message: str,
    history: list[Message],
    llm_callable: LLMCallable | None = None,
) -> str:
    """Answer return and refund questions using policy text only."""

    policy_text = load_return_policy()
    prompt = build_return_policy_prompt(policy_text)
    try:
        if llm_callable:
            return llm_callable(prompt, history, message)
        return call_claude(prompt, history, message, max_tokens=250)
    except LLMServiceError as exc:
        err = str(exc)
        if "API_KEY is missing" in err:
            return (
                "AI is not configured yet. Please set GROQ_API_KEY, GEMINI_API_KEY, "
                "or ANTHROPIC_API_KEY in .env and restart the server."
            )
        if "quota exceeded" in err.lower():
            return (
                "AI quota is exceeded for your current key/project. "
                "Please check provider usage limits or billing, then retry."
            )
        return "I could not reach the AI service right now. Please try again shortly."
