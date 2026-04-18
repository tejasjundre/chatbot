"""Tests for rate limiting utilities."""

from __future__ import annotations

from bot.rate_limit import SlidingWindowRateLimiter


def test_rate_limiter_blocks_after_limit() -> None:
    """Limiter should deny requests that exceed the configured window budget."""

    limiter = SlidingWindowRateLimiter(limit=2, window_seconds=60)
    allowed_1, retry_1 = limiter.check("demo")
    allowed_2, retry_2 = limiter.check("demo")
    allowed_3, retry_3 = limiter.check("demo")

    assert allowed_1 is True
    assert retry_1 == 0
    assert allowed_2 is True
    assert retry_2 == 0
    assert allowed_3 is False
    assert retry_3 >= 1

