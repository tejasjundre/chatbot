"""Intent classification and feature routing."""

from __future__ import annotations

import re
from collections.abc import Callable

from bot.conversation import Message, conversation_manager
from bot.guidance import build_help_message, is_help_request, suggest_follow_ups
from bot.llm import LLMServiceError, call_claude
from bot.prompts import build_intent_prompt
from features import (
    add_to_cart,
    auto_reorder,
    comparison,
    generative_search,
    order_status,
    price_tracking,
    product_qa,
    return_policy,
    sentiment,
)

LLMCallable = Callable[[str, list[Message], str], str]
VALID_INTENTS = {
    "product_qa",
    "order_status",
    "return_policy",
    "search",
    "sentiment",
    "comparison",
    "add_to_cart",
    "price_track",
    "reorder",
    "unknown",
}


def _heuristic_intent(message: str) -> str:
    """Fallback rule-based classifier used when AI classification is unavailable."""

    text = message.lower()
    if any(token in text for token in ["ord-", "order", "delivery", "shipped"]):
        return "order_status"
    if any(token in text for token in ["return", "refund", "exchange"]):
        return "return_policy"
    if any(token in text for token in ["compare", "vs", "versus"]):
        return "comparison"
    if any(token in text for token in ["review", "sentiment", "people think"]):
        return "sentiment"
    if any(token in text for token in ["under", "show me", "find", "search"]):
        return "search"
    if any(token in text for token in ["add to cart", "cart"]):
        return "add_to_cart"
    if any(token in text for token in ["price drop", "track price", "notify"]):
        return "price_track"
    if "reorder" in text:
        return "reorder"
    if any(token in text for token in ["spec", "feature", "does", "have"]):
        return "product_qa"
    return "unknown"


def classify_intent(
    message: str,
    history: list[Message],
    llm_callable: LLMCallable | None = None,
) -> str:
    """Classify a user message into one of the supported intents."""

    prompt = build_intent_prompt()
    try:
        raw = (
            llm_callable(prompt, history, message)
            if llm_callable
            else call_claude(prompt, history, message, max_tokens=20)
        )
        first_token = raw.strip().lower().replace("-", "_").split()[0]
        normalized = re.sub(r"[^a-z_]", "", first_token)
        if normalized in VALID_INTENTS:
            return normalized
    except (LLMServiceError, IndexError):
        return _heuristic_intent(message)
    return _heuristic_intent(message)


def route_message(session_id: str, message: str) -> tuple[str, str]:
    """Route the message to the right feature module and return intent + reply."""

    result = route_message_with_meta(session_id, message)
    return result["intent"], result["reply"]


def route_message_with_meta(session_id: str, message: str) -> dict[str, object]:
    """Route a message and return intent, reply, and follow-up suggestions."""

    history = conversation_manager.get_history(session_id)
    fallback = (
        "I can help with products, orders, returns, search, and comparisons. "
        "Try: 'Track ORD-1042', 'Show me headphones under 3000', or "
        "'Compare SoundMax Pro vs AirMax 3000'."
    )

    if is_help_request(message):
        intent = "unknown"
        reply = build_help_message()
    else:
        intent = classify_intent(message, history)
        if intent == "product_qa":
            reply = product_qa.answer_product_question(message, history)
        elif intent == "order_status":
            reply = order_status.get_order_status(message)
        elif intent == "return_policy":
            reply = return_policy.answer_return_policy_question(message, history)
        elif intent == "search":
            reply = generative_search.search_products(message, history)
        elif intent == "sentiment":
            reply = sentiment.summarize_product_sentiment(message, history)
        elif intent == "comparison":
            reply = comparison.compare_products(message)
        elif intent == "add_to_cart":
            reply = add_to_cart.handle_add_to_cart(session_id, message)
        elif intent == "price_track":
            reply = price_tracking.handle_price_tracking(message)
        elif intent == "reorder":
            reply = auto_reorder.suggest_reorder(message)
        else:
            intent = "unknown"
            reply = fallback

    conversation_manager.append(session_id, "user", message)
    conversation_manager.append(session_id, "assistant", reply)
    return {
        "intent": intent,
        "reply": reply,
        "suggestions": suggest_follow_ups(intent),
    }
