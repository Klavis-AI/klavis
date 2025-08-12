import time
import math
from typing import Dict
from datetime import datetime, timedelta
import asyncio

class FreshdeskRateLimiter:
    def __init__(self):
        self.rate_limit_total = 50 
        self.rate_limit_remaining = 50
        self.rate_limit_reset = 60 
        self.last_request_time = 0
        self.retry_after = 0
        self.window_start = time.time()
        self.requests_in_window = 0

    def update_from_headers(self, headers: Dict[str, str]) -> None:
        """Update rate limit state from response headers"""
        now = time.time()
        
        # Reset window if we're in a new minute
        if now - self.window_start >= 60:
            self.window_start = now
            self.requests_in_window = 0

        if 'X-RateLimit-Total' in headers:
            self.rate_limit_total = int(headers['X-RateLimit-Total'])
        if 'X-RateLimit-Remaining' in headers:
            self.rate_limit_remaining = int(headers['X-RateLimit-Remaining'])
        if 'Retry-After' in headers:
            self.retry_after = int(headers['Retry-After'])
        
        self.requests_in_window += 1
        self.last_request_time = now

    def get_sleep_time(self) -> float:
        """Calculate how long to sleep before next request"""
        now = time.time()
        
        # If we hit rate limit, use Retry-After
        if self.retry_after > 0:
            return self.retry_after
        
        # Calculate time since last request to enforce minimum delay
        time_since_last = now - self.last_request_time
        min_delay = 0.1 
        sleep_time = max(0, min_delay - time_since_last)
        
        # If we're approaching the rate limit, let's slow down
        if self.rate_limit_remaining < self.rate_limit_total * 0.1:  
            time_left_in_window = 60 - (now - self.window_start)
            if time_left_in_window > 0:
                # Distribute remaining requests over time left
                sleep_time = max(sleep_time, time_left_in_window / (self.rate_limit_remaining + 1))
        
        return sleep_time

    async def wait_for_capacity(self, required_requests: int = 1) -> None:
        """Wait until we have capacity to make the requested number of API calls"""
        if self.rate_limit_remaining < required_requests:
            sleep_time = self.get_sleep_time()
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)


rate_limiter = FreshdeskRateLimiter()