"""Phase 2: Generative product search."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from bot.conversation import Message
from bot.llm import LLMServiceError, call_claude
from bot.prompts import build_search_prompt
from features.product_qa import load_products

LLMCallable = Callable[[str, list[Message], str], str]


def _extract_price_limit(message: str) -> int | None:
    """Extract an 'under X' style numeric price limit from user text."""

    match = re.search(
        r"(?:under|below|less than)\s*(?:inr|rs\.?|rupees)?\s*(\d{2,6})",
        message.lower(),
    )
    return int(match.group(1)) if match else None


def _extract_category(message: str, products: list[dict[str, Any]]) -> str | None:
    """Infer a category mention from the query and known product categories."""

    lowered = message.lower()
    categories = {str(item["category"]).lower() for item in products}
    for category in categories:
        singular = category[:-1] if category.endswith("s") else category
        if category in lowered or singular in lowered:
            return category
    return None


def filter_products(
    message: str, products: list[dict[str, Any]] | None = None
) -> list[dict[str, Any]]:
    """Filter products by query hints such as category, stock, and budget."""

    catalog = products or load_products()
    cap = _extract_price_limit(message)
    category = _extract_category(message, catalog)
    filtered: list[dict[str, Any]] = []
    for item in catalog:
        if not item.get("stock", False):
            continue
        if cap is not None and int(item["price"]) > cap:
            continue
        if category and str(item["category"]).lower() != category:
            continue
        filtered.append(item)
    return sorted(filtered, key=lambda value: int(value["price"]))


def search_products(
    message: str,
    history: list[Message],
    llm_callable: LLMCallable | None = None,
) -> str:
    """Return top search matches and a concise natural-language summary."""

    matches = filter_products(message)[:3]
    if not matches:
        return "I could not find matching in-stock products for that request."
    prompt = build_search_prompt(message, matches)
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
            lines = ["AI quota is currently exceeded. Showing deterministic matches instead:"]
            for index, product in enumerate(matches, start=1):
                lines.append(
                    f"{index}. {product['name']} - INR {product['price']} ({product['category']})"
                )
            return "\n".join(lines)
        lines = ["I found these options:"]
        for index, product in enumerate(matches, start=1):
            lines.append(
                f"{index}. {product['name']} - INR {product['price']} ({product['category']})"
            )
        return "\n".join(lines)
