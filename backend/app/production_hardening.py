import time
from collections import defaultdict, deque
from threading import Lock

class SlidingWindowRateLimiter:
    def __init__(self, limit=30, window_seconds=60):
        self.limit=max(1,int(limit)); self.window_seconds=max(1,int(window_seconds))
        self._events=defaultdict(deque); self._lock=Lock()
    def allow(self,key):
        now=time.monotonic()
        with self._lock:
            q=self._events[key]; cutoff=now-self.window_seconds
            while q and q[0]<=cutoff:q.popleft()
            if len(q)>=self.limit:return False
            q.append(now);return True
    def clear(self):
        with self._lock:self._events.clear()

def safe_rate_limit_key(user_id,fallback):
    return f"user:{user_id}" if user_id is not None else f"anon:{fallback}"
