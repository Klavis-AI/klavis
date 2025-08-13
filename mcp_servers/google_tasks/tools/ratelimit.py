import time
from collections import defaultdict, deque


class TooManyRequests(Exception):
    pass


class RateLimiter:
    def __init__(self, max_calls: int, period_seconds: int):
        self.max = max_calls
        self.period = period_seconds
        self.calls = defaultdict(deque)  # key -> deque[timestamps]

    def hit(self, key: str):
        now = time.monotonic()
        dq = self.calls[key]
        # purge old calls
        while dq and (now - dq[0]) > self.period:
            dq.popleft()
        if len(dq) >= self.max:
            raise TooManyRequests(f"Rate limit exceeded for '{key}': {self.max} calls per {self.period}s.")
        dq.append(now)