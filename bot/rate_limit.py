"""Simple in-memory sliding-window rate limiter."""

from __future__ import annotations

from collections import defaultdict, deque
from math import ceil
from threading import Lock
from time import monotonic


class SlidingWindowRateLimiter:
    """Rate limiter that tracks request timestamps per key."""

    def __init__(self, limit: int, window_seconds: int = 60) -> None:
        """Initialize limiter with request count and window size."""

        self.limit = max(1, limit)
        self.window_seconds = max(1, window_seconds)
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str) -> tuple[bool, int]:
        """Check whether a request is allowed and return retry-after seconds."""

        now = monotonic()
        with self._lock:
            queue = self._events[key]
            cutoff = now - self.window_seconds
            while queue and queue[0] <= cutoff:
                queue.popleft()
            if len(queue) >= self.limit:
                retry_after = max(1, ceil(self.window_seconds - (now - queue[0])))
                return False, retry_after
            queue.append(now)
            return True, 0

