import asyncio
import time
from collections import defaultdict, deque
from config import RATE_LIMIT_ATTEMPTS, RATE_LIMIT_WINDOW


class RateLimiter:
    def __init__(self, max_attempts=RATE_LIMIT_ATTEMPTS, window=RATE_LIMIT_WINDOW):
        self._max    = max_attempts
        self._window = window
        self._buckets: dict[int, deque] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def is_allowed(self, user_id: int) -> bool:
        now = time.monotonic()
        async with self._lock:
            dq = self._buckets[user_id]
            while dq and now - dq[0] > self._window:
                dq.popleft()
            if len(dq) >= self._max:
                return False
            dq.append(now)
            return True

    async def wait_seconds(self, user_id: int) -> int:
        now = time.monotonic()
        async with self._lock:
            dq = self._buckets.get(user_id)
            if not dq:
                return 0
            return max(0, int(self._window - (now - dq[0])) + 1)


rate_limiter = RateLimiter()
