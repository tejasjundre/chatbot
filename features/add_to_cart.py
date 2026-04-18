"""Phase 3 stub: Add-to-cart simulation."""

from __future__ import annotations

from features.product_qa import load_products

CARTS: dict[str, list[str]] = {}


def _find_product_name(message: str) -> str | None:
    """Find a product name mention in the user message."""

    lowered = message.lower()
    for product in load_products():
        name = str(product["name"])
        if name.lower() in lowered:
            return name
    return None


def handle_add_to_cart(session_id: str, message: str) -> str:
    """Simulate add-to-cart behavior in memory for a chat session."""

    if "show" in message.lower() and "cart" in message.lower():
        items = CARTS.get(session_id, [])
        return f"Your cart has: {', '.join(items)}." if items else "Your cart is empty."

    product_name = _find_product_name(message)
    if not product_name:
        return (
            "Cart feature is in progress. Please mention the exact product name to add."
        )

    # TODO: Replace in-memory state with persistent user cart storage.
    CARTS.setdefault(session_id, []).append(product_name)
    return f"Added {product_name} to your cart (simulated)."

