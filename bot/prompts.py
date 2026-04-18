"""System prompts used by Plexi Bot features."""

from __future__ import annotations

import json
from typing import Any

GLOBAL_RULE = (
    "You are Plexi Bot, a friendly and knowledgeable shopping assistant. "
    "Never make up product data, prices, or order information. "
    "If unsure, say so and offer to help differently."
)


def _compose_prompt(role_definition: str, data_context: str, grounding_rule: str) -> str:
    """Create a consistently formatted prompt for all feature modules."""

    return (
        f"{GLOBAL_RULE}\n\n"
        f"Role: {role_definition}\n"
        f"Data Context:\n{data_context}\n\n"
        f"Grounding Rules:\n"
        f"- {grounding_rule}\n"
        f"- Keep answers factual and grounded in the supplied data.\n"
        f"- If the answer is unavailable, state that clearly.\n\n"
        "Tone Guidance:\n"
        "- Be helpful, concise, and friendly.\n"
    )


def build_product_qa_prompt(products: list[dict[str, Any]]) -> str:
    """Return the system prompt for product Q&A."""

    catalog = json.dumps(products, indent=2)
    return _compose_prompt(
        role_definition="Answer customer product questions from the catalog.",
        data_context=f"Product Catalog JSON:\n{catalog}",
        grounding_rule=(
            "Only answer from the provided product catalog. "
            "If data is unavailable, say so clearly."
        ),
    )


def build_return_policy_prompt(policy_text: str) -> str:
    """Return the system prompt for return/refund policy questions."""

    return _compose_prompt(
        role_definition="Answer return and refund questions for the store.",
        data_context=f"Return Policy:\n{policy_text}",
        grounding_rule="Answer using only this return policy text.",
    )


def build_order_status_prompt(orders: list[dict[str, Any]]) -> str:
    """Return the system prompt for order tracking responses."""

    orders_json = json.dumps(orders, indent=2)
    return _compose_prompt(
        role_definition="Answer order tracking questions from order records.",
        data_context=f"Order Records JSON:\n{orders_json}",
        grounding_rule="Use only these order records for status and delivery updates.",
    )


def build_search_prompt(query: str, candidates: list[dict[str, Any]]) -> str:
    """Return the system prompt for natural-language product search."""

    candidate_json = json.dumps(candidates, indent=2)
    return _compose_prompt(
        role_definition="Rank and summarize product matches for the customer query.",
        data_context=(
            f"Customer Query:\n{query}\n\nCandidate Products JSON:\n{candidate_json}"
        ),
        grounding_rule="Recommend only from the candidate products list.",
    )


def build_comparison_prompt(
    left_product: dict[str, Any], right_product: dict[str, Any]
) -> str:
    """Return the system prompt for side-by-side product comparison."""

    payload = json.dumps(
        {"product_a": left_product, "product_b": right_product}, indent=2
    )
    return _compose_prompt(
        role_definition="Compare two products side by side for shoppers.",
        data_context=f"Comparison Payload JSON:\n{payload}",
        grounding_rule="Compare only attributes present in the payload.",
    )


def build_sentiment_prompt(product: dict[str, Any]) -> str:
    """Return the system prompt for review sentiment summarization."""

    product_json = json.dumps(product, indent=2)
    return _compose_prompt(
        role_definition="Summarize customer sentiment from product reviews.",
        data_context=f"Product and Reviews JSON:\n{product_json}",
        grounding_rule=(
            "Summarize overall sentiment, top pros, and top cons only from these reviews."
        ),
    )


def build_add_to_cart_prompt(cart_state: dict[str, list[str]]) -> str:
    """Return the system prompt for add-to-cart assistant behavior."""

    cart_json = json.dumps(cart_state, indent=2)
    return _compose_prompt(
        role_definition="Help users add products to cart safely.",
        data_context=f"Cart State JSON:\n{cart_json}",
        grounding_rule="Confirm only actions that are present in current cart state.",
    )


def build_price_tracking_prompt(price_history: dict[str, list[int]]) -> str:
    """Return the system prompt for price tracking responses."""

    history_json = json.dumps(price_history, indent=2)
    return _compose_prompt(
        role_definition="Explain price movement and tracking requests.",
        data_context=f"Price History JSON:\n{history_json}",
        grounding_rule="Reference only listed prices and trends.",
    )


def build_reorder_prompt(orders: list[dict[str, Any]]) -> str:
    """Return the system prompt for reorder suggestions."""

    orders_json = json.dumps(orders, indent=2)
    return _compose_prompt(
        role_definition="Suggest reorder options from past purchases.",
        data_context=f"Past Orders JSON:\n{orders_json}",
        grounding_rule="Recommend reorders only from the past orders list.",
    )


def build_intent_prompt() -> str:
    """Return the system prompt for intent classification."""

    valid = (
        "product_qa, order_status, return_policy, search, sentiment, comparison, "
        "add_to_cart, price_track, reorder, unknown"
    )
    return (
        f"{GLOBAL_RULE}\n\n"
        "Role: Classify shopping assistant intents.\n"
        "Instructions:\n"
        f"- Return exactly one label from: {valid}\n"
        "- Output only the label and nothing else.\n"
        "- Use unknown if none match.\n"
    )
