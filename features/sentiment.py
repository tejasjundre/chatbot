"""Phase 2: Review sentiment summarization."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from bot.conversation import Message
from bot.llm import LLMServiceError, call_claude
from bot.prompts import build_sentiment_prompt
from features.product_qa import load_products

LLMCallable = Callable[[str, list[Message], str], str]


def _match_product_from_text(
    message: str, products: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """Match the target product by finding its name in the user message."""

    lowered = message.lower()
    for product in products:
        name = str(product.get("name", "")).lower()
        if name and name in lowered:
            return product
    return None


def summarize_product_sentiment(
    message: str,
    history: list[Message],
    llm_callable: LLMCallable | None = None,
) -> str:
    """Summarize review sentiment for a matched product."""

    products = load_products()
    product = _match_product_from_text(message, products)
    if not product:
        return "Please mention the exact product name so I can summarize its reviews."
    prompt = build_sentiment_prompt(product)
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
                "AI quota is currently exceeded for your key/project, so sentiment "
                "summarization is temporarily unavailable."
            )
        reviews = product.get("reviews", [])
        positives = [text for text in reviews if any(k in text.lower() for k in ["good", "great", "amazing", "comfortable", "love"])]
        negatives = [text for text in reviews if any(k in text.lower() for k in ["bad", "poor", "drain", "slow", "issue"])]
        return (
            f"Sentiment for {product['name']}: mixed.\n"
            f"Top pros: {', '.join(positives[:2]) or 'Not enough review detail'}.\n"
            f"Top cons: {', '.join(negatives[:2]) or 'No strong recurring concerns'}."
        )
