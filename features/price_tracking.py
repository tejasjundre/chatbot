"""Phase 3 stub: Price tracking simulation."""

from __future__ import annotations

PRICE_HISTORY: dict[str, list[int]] = {
    "soundmax pro": [3499, 3299, 2999],
    "airmax 3000": [3999, 3499, 3199],
    "zenbuds lite": [2499, 2199, 1999],
}


def handle_price_tracking(message: str) -> str:
    """Return a simulated price-history response for a product."""

    lowered = message.lower()
    for product_name, prices in PRICE_HISTORY.items():
        if product_name in lowered:
            current = prices[-1]
            lowest = min(prices)
            # TODO: Add real subscription and scheduled price monitoring.
            return (
                f"{product_name.title()} current price is INR {current}. "
                f"Recent low was INR {lowest}. "
                "I can notify you in a future release when prices drop."
            )
    return "Price tracking is a stub right now. Mention a product name to simulate."

