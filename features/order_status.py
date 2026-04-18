"""Phase 1: Order status lookup feature."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from bot.data_store import get_orders

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "orders.json"


def load_orders(path: Path = DATA_FILE) -> list[dict[str, Any]]:
    """Load order records from JSON."""

    if path == DATA_FILE:
        return get_orders()
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def find_order(query: str, orders: list[dict[str, Any]] | None = None) -> dict[str, Any] | None:
    """Find an order by order ID or customer name contained in the query."""

    order_list = orders or load_orders()
    match = re.search(r"ORD-\d+", query, re.IGNORECASE)
    if match:
        target_id = match.group(0).upper()
        for order in order_list:
            if str(order.get("order_id", "")).upper() == target_id:
                return order
    lowered = query.lower()
    for order in order_list:
        customer = str(order.get("customer", "")).lower()
        if customer and (customer in lowered or lowered in customer):
            return order
    return None


def get_order_status(message: str) -> str:
    """Return a friendly status summary for a matched order."""

    order = find_order(message)
    if not order:
        return (
            "I could not find that order. Please share a valid order ID like "
            "ORD-1042 or the customer name."
        )
    items = ", ".join(order.get("items", []))
    return (
        f"Order {order['order_id']} for {order['customer']} is {order['status']}. "
        f"Estimated delivery: {order['estimated_delivery']}. Items: {items}."
    )
