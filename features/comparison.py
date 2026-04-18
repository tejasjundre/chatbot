"""Phase 2: Product comparison feature."""

from __future__ import annotations

import re
from typing import Any

from features.product_qa import get_product_by_name, load_products


def _extract_targets(message: str) -> tuple[str | None, str | None]:
    """Extract two product names from a comparison request."""

    match = re.search(
        r"compare\s+(.+?)\s+(?:vs|versus|and)\s+(.+?)[?.!]*$",
        message,
        flags=re.IGNORECASE,
    )
    if not match:
        return None, None
    left = match.group(1).strip()
    right = match.group(2).strip()
    return left, right


def _spec(product: dict[str, Any], key: str) -> str:
    """Read a product spec value safely as text."""

    specs = product.get("specs", {})
    value = specs.get(key, "N/A")
    return "Yes" if value is True else "No" if value is False else str(value)


def compare_products(message: str) -> str:
    """Generate a side-by-side comparison table for two products."""

    left_query, right_query = _extract_targets(message)
    if not left_query or not right_query:
        return "Please use format: Compare Product A vs Product B."
    catalog = load_products()
    left = get_product_by_name(left_query, catalog)
    right = get_product_by_name(right_query, catalog)
    missing = []
    if not left:
        missing.append(left_query)
    if not right:
        missing.append(right_query)
    if missing:
        missing_text = ", ".join(missing)
        return f"I could not find: {missing_text}. Please check the product names."

    rows = [
        "| Feature | Product A | Product B |",
        "|---|---|---|",
        f"| Name | {left['name']} | {right['name']} |",
        f"| Category | {left['category']} | {right['category']} |",
        f"| Price | INR {left['price']} | INR {right['price']} |",
        f"| Battery | {_spec(left, 'battery')} | {_spec(right, 'battery')} |",
        f"| Bluetooth | {_spec(left, 'bluetooth')} | {_spec(right, 'bluetooth')} |",
        f"| Noise Cancellation | {_spec(left, 'noise_cancellation')} | {_spec(right, 'noise_cancellation')} |",
        f"| In Stock | {'Yes' if left['stock'] else 'No'} | {'Yes' if right['stock'] else 'No'} |",
    ]
    return "\n".join(rows)

