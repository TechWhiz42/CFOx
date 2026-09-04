import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request, status


class SlidingWindowRateLimiter:
    def __init__(self, limit=30, window_seconds=60):
        self.limit = max(1, int(limit))
        self.window_seconds = max(1, int(window_seconds))
        self._events = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key):
        now = time.monotonic()

        with self._lock:
            events = self._events[key]
            cutoff = now - self.window_seconds

            while events and events[0] <= cutoff:
                events.popleft()

            if len(events) >= self.limit:
                return False

            events.append(now)
            return True

    def clear(self):
        with self._lock:
            self._events.clear()


auth_limiter = SlidingWindowRateLimiter(limit=10, window_seconds=60)
ai_limiter = SlidingWindowRateLimiter(limit=20, window_seconds=60)
webhook_limiter = SlidingWindowRateLimiter(limit=120, window_seconds=60)


def request_rate_limit_key(request: Request, scope: str) -> str:
    host = request.client.host if request.client else "unknown"
    return f"{scope}:ip:{host}"


def user_rate_limit_key(user_id: int, scope: str) -> str:
    return f"{scope}:user:{user_id}"


def safe_rate_limit_key(user_id, fallback):
    return f"user:{user_id}" if user_id is not None else f"anon:{fallback}"


def enforce_rate_limit(limiter: SlidingWindowRateLimiter, key: str) -> None:
    if not limiter.allow(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please wait and try again.",
        )