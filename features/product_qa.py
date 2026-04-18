"""Phase 1: Product Q&A feature."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from bot.conversation import Message
from bot.data_store import get_products
from bot.llm import LLMServiceError, call_claude
from bot.prompts import build_product_qa_prompt

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "products.json"
LLMCallable = Callable[[str, list[Message], str], str]


def load_products(path: Path = DATA_FILE) -> list[dict[str, Any]]:
    """Load the product catalog from JSON."""

    if path == DATA_FILE:
        return get_products()
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def get_product_by_name(
    name: str, products: list[dict[str, Any]] | None = None
) -> dict[str, Any] | None:
    """Find a product by exact or partial name match."""

    catalog = products or load_products()
    needle = name.lower().strip()
    for product in catalog:
        product_name = str(product.get("name", "")).lower()
        if product_name == needle or needle in product_name:
            return product
    return None


def answer_product_question(
    message: str,
    history: list[Message],
    llm_callable: LLMCallable | None = None,
) -> str:
    """Answer product questions grounded in the catalog only."""

    products = load_products()
    prompt = build_product_qa_prompt(products)
    try:
        if llm_callable:
            return llm_callable(prompt, history, message)
        return call_claude(prompt, history, message, max_tokens=300)
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
        return "I could not access the AI service right now. Please try again in a moment."
