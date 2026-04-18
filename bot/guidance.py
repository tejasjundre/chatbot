"""User guidance utilities: capabilities, examples, and follow-up suggestions."""

from __future__ import annotations

from collections import OrderedDict

CAPABILITIES: OrderedDict[str, dict[str, object]] = OrderedDict(
    [
        (
            "Product Q&A",
            {
                "intent": "product_qa",
                "description": "Ask about specs, price, stock, and product details.",
                "examples": [
                    "Does AirMax 3000 support Bluetooth?",
                    "What is the price of SoundMax Pro?",
                ],
            },
        ),
        (
            "Order Tracking",
            {
                "intent": "order_status",
                "description": "Track order status using order ID or customer name.",
                "examples": [
                    "Track ORD-1042",
                    "Where is Tejas's order?",
                ],
            },
        ),
        (
            "Returns and Refunds",
            {
                "intent": "return_policy",
                "description": "Get policy-grounded answers about return windows and refunds.",
                "examples": [
                    "How many days do I have to return a product?",
                    "Do you refund damaged items?",
                ],
            },
        ),
        (
            "Search and Recommendations",
            {
                "intent": "search",
                "description": "Find products using natural language filters.",
                "examples": [
                    "Show me wireless headphones under 3000",
                    "Find in-stock earbuds below 2500",
                ],
            },
        ),
        (
            "Reviews and Comparison",
            {
                "intent": "sentiment",
                "description": "Summarize reviews and compare products side by side.",
                "examples": [
                    "What do people think about SoundMax Pro?",
                    "Compare SoundMax Pro vs AirMax 3000",
                ],
            },
        ),
    ]
)

HELP_TRIGGERS = {
    "help",
    "what can you do",
    "how do i use this",
    "how to use",
    "guide me",
    "examples",
    "start",
}

FOLLOW_UP_BY_INTENT: dict[str, list[str]] = {
    "product_qa": ["Compare SoundMax Pro vs AirMax 3000", "Show similar products under 3000"],
    "order_status": ["Track ORD-1043", "What does shipped status mean?"],
    "return_policy": ["Is return shipping free?", "When will I get my refund?"],
    "search": ["Show me earbuds under 2500", "Compare top 2 options"],
    "sentiment": ["Compare SoundMax Pro vs AirMax 3000", "Is SoundMax Pro worth it?"],
    "comparison": ["Show me cheaper alternatives", "What do reviews say about Product A?"],
    "add_to_cart": ["Show my cart", "Add AirMax 3000 to cart"],
    "price_track": ["Track price for SoundMax Pro", "What is the recent low price?"],
    "reorder": ["Reorder for Tejas", "Show previous items for Asha"],
    "unknown": ["Track ORD-1042", "Show me headphones under 3000"],
}


def is_help_request(message: str) -> bool:
    """Return True when the user is asking for guidance/examples."""

    text = message.lower().strip()
    return any(trigger in text for trigger in HELP_TRIGGERS)


def build_help_message() -> str:
    """Build a concise help message with practical starter prompts."""

    return (
        "I can help you in 5 ways:\n"
        "1) Product Q&A - ask specs, price, stock.\n"
        "2) Order Tracking - use order ID like ORD-1042.\n"
        "3) Return Policy - ask refund/return questions.\n"
        "4) Smart Search - natural language filters like budget/category.\n"
        "5) Reviews & Compare - summarize sentiment or compare two products.\n\n"
        "Try these:\n"
        "- Show me wireless headphones under 3000\n"
        "- Track ORD-1042\n"
        "- Compare SoundMax Pro vs AirMax 3000"
    )


def capabilities_payload() -> dict[str, object]:
    """Return structured capabilities for frontend rendering."""

    cards = []
    for title, details in CAPABILITIES.items():
        cards.append({"title": title, **details})
    return {
        "title": "Plexi Bot Capabilities",
        "summary": "Use natural language to shop, track orders, and analyze products.",
        "cards": cards,
    }


def suggest_follow_ups(intent: str) -> list[str]:
    """Return suggested follow-up prompts for a detected intent."""

    return FOLLOW_UP_BY_INTENT.get(intent, FOLLOW_UP_BY_INTENT["unknown"])

