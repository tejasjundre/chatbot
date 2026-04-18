"""Unit tests for Plexi Bot features."""

from __future__ import annotations

from uuid import uuid4

from bot.guidance import suggest_follow_ups
from bot.router import classify_intent, route_message
from features.order_status import find_order
from features.product_qa import get_product_by_name, load_products
from features.sentiment import summarize_product_sentiment


def test_product_lookup_finds_soundmax() -> None:
    """Product lookup should return the catalog product by name."""

    product = get_product_by_name("SoundMax Pro", load_products())
    assert product is not None
    assert product["id"] == "P001"


def test_order_lookup_by_order_id() -> None:
    """Order lookup should resolve by ORD-* identifier."""

    order = find_order("Track ORD-1042")
    assert order is not None
    assert order["customer"] == "Tejas"


def test_intent_classification_uses_valid_label() -> None:
    """Classifier should accept model output when it is a valid intent."""

    mock_llm = lambda system, history, message: "order_status"
    intent = classify_intent("Where is my order?", [], llm_callable=mock_llm)
    assert intent == "order_status"


def test_unknown_intent_fallback() -> None:
    """Classifier should fall back to unknown when no intent is matched."""

    mock_llm = lambda system, history, message: "banana"
    intent = classify_intent("Tell me a bedtime story", [], llm_callable=mock_llm)
    assert intent == "unknown"


def test_sentiment_summary_response() -> None:
    """Sentiment feature should return a generated summary for matched products."""

    mock_llm = lambda system, history, message: "Overall sentiment is positive."
    reply = summarize_product_sentiment(
        "What do people think about SoundMax Pro?",
        [],
        llm_callable=mock_llm,
    )
    assert "positive" in reply.lower()


def test_route_message_unknown_intent_reply() -> None:
    """Router should provide helpful fallback for unsupported requests."""

    session_id = str(uuid4())
    intent, reply = route_message(session_id, "Can you write me a poem?")
    assert intent == "unknown"
    assert "I can help with products" in reply


def test_help_request_returns_onboarding_message() -> None:
    """Help-like messages should return guided usage information."""

    session_id = str(uuid4())
    intent, reply = route_message(session_id, "help me use this bot")
    assert intent == "unknown"
    assert "I can help you in 5 ways" in reply


def test_follow_up_suggestions_for_order_status() -> None:
    """Order status intent should expose relevant next-step suggestions."""

    suggestions = suggest_follow_ups("order_status")
    assert len(suggestions) >= 1
    assert "Track ORD-" in suggestions[0]
