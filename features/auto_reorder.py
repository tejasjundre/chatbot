"""Phase 3 stub: Auto reorder suggestions."""

from __future__ import annotations

from features.order_status import load_orders


def suggest_reorder(message: str) -> str:
    """Suggest a reorder option from past orders."""

    lowered = message.lower()
    orders = load_orders()
    for order in orders:
        customer = str(order.get("customer", "")).lower()
        if customer and customer in lowered:
            items = ", ".join(order.get("items", []))
            # TODO: Add confirmation flow and checkout handoff.
            return (
                f"Last order for {order['customer']} was {order['order_id']} "
                f"with items: {items}. Reply 'reorder now' to simulate."
            )
    latest = orders[0]
    fallback_items = ", ".join(latest.get("items", []))
    return (
        "Auto reorder is currently a stub. "
        f"For example, {latest['customer']} previously ordered {fallback_items}."
    )

