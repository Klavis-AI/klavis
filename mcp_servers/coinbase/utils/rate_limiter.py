import asyncio
import functools
import logging
import time

from typing import Any, Callable, Optional
from contextlib import asynccontextmanager

from tools.constants import (
    COINBASE_DEFAULT_RATE_LIMIT,
    COINBASE_MARKET_DATA_RATE_LIMIT,
    COINBASE_ACCOUNTS_RATE_LIMIT,
    COINBASE_PRODUCTS_RATE_LIMIT,
    COINBASE_MAX_RETRY_ATTEMPTS,
    COINBASE_INITIAL_DELAY,
    COINBASE_MAX_DELAY,
    COINBASE_BACKOFF_FACTOR,
)

logger = logging.getLogger(__name__)


_rate_limiters = {}


class RateLimitConfig:
    """Configuration class for rate limiting settings."""

    def __init__(self):
        # Default rate limit for Coinbase API
        self.default_max_requests_per_second = COINBASE_DEFAULT_RATE_LIMIT

        # API-specific rate limits with smart defaults
        # Market API: 10,000 per hour = 2.78 per second, rounded down to 2 for safety
        self.market_data_rate_limit = COINBASE_MARKET_DATA_RATE_LIMIT

        # Accounts API: 10,000 per hour = 2.78 per second, rounded down to 2 for safety
        self.accounts_rate_limit = COINBASE_ACCOUNTS_RATE_LIMIT

        # Products API: 10 per second
        self.products_rate_limit = COINBASE_PRODUCTS_RATE_LIMIT

        # Retry settings
        self.max_retry_attempts = COINBASE_MAX_RETRY_ATTEMPTS
        self.initial_delay = COINBASE_INITIAL_DELAY
        self.max_delay = COINBASE_MAX_DELAY
        self.backoff_factor = COINBASE_BACKOFF_FACTOR


class TokenBucketRateLimiter:
    """
    Token Bucket Rate Limiter Implementation

    The token bucket algorithm allows for a burst of traffic up to the bucket capacity,
    while maintaining a steady rate of token refill.
    """

    def __init__(
        self,
        tokens_per_second: int,
        bucket_capacity: Optional[int] = None
    ):
        """
        Initialize token bucket rate limiter.

        Args:
            tokens_per_second: Rate at which tokens are refilled
            bucket_capacity: Maximum number of tokens in bucket (defaults to tokens_per_second)
        """
        self.tokens_per_second = tokens_per_second
        self.bucket_capacity = bucket_capacity or tokens_per_second
        self.tokens = self.bucket_capacity  # Start with full bucket
        self.last_refill_time = time.time()

    def _refill_tokens(self):
        """Refill tokens based on time elapsed since last refill."""
        current_time = time.time()
        time_elapsed = current_time - self.last_refill_time

        # Calculate tokens to add
        tokens_to_add = time_elapsed * self.tokens_per_second

        # Update tokens (don't exceed capacity)
        self.tokens = min(self.bucket_capacity, self.tokens + tokens_to_add)
        self.last_refill_time = current_time

    def try_consume_token(self) -> bool:
        """
        Try to consume a token from the bucket.

        Returns:
            True if token was consumed, False if bucket is empty
        """
        self._refill_tokens()

        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False

    def get_wait_time(self) -> float:
        """
        Calculate how long to wait before a token will be available.

        Returns:
            Time in seconds to wait
        """
        self._refill_tokens()

        if self.tokens >= 1:
            return 0.0

        # Calculate time until next token is available
        tokens_needed = 1 - self.tokens
        wait_time = tokens_needed / self.tokens_per_second

        return max(wait_time, 0.1)  # Minimum 0.1 second wait


class RateLimiter:
    def __init__(
        self,
        max_requests_per_second: Optional[int] = None
    ):
        self.max_requests_per_second = max_requests_per_second or config.default_max_requests_per_second
        self.token_bucket = TokenBucketRateLimiter(
            self.max_requests_per_second
        )

    def _is_rate_limited(self) -> bool:
        """Check if we're currently rate limited using token bucket."""
        return not self.token_bucket.try_consume_token()

    def _calculate_wait_time(self) -> float:
        """Calculate how long to wait before next request is allowed."""
        return self.token_bucket.get_wait_time()

    def _add_request(self):
        """Record a new request (not needed for token bucket, but kept for compatibility)."""
        pass

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry with exponential backoff."""
        delay = min(
            config.initial_delay * (config.backoff_factor ** (attempt - 1)),
            config.max_delay
        )
        return delay

    def _is_rate_limit_error(self, error: Exception) -> bool:
        """Check if the error is a rate limit error."""
        error_str = str(error).lower()
        return any(phrase in error_str for phrase in [
            'rate limit',
            '429',
            'too many requests',
            'quota exceeded',
            'throttled'
        ])

    async def _delay(self, seconds: float):
        """Async delay function."""
        await asyncio.sleep(seconds)

    async def with_retry(self, operation: Callable, context: str = "API request") -> Any:
        """
        Execute an operation with retry logic and rate limiting.

        Args:
            operation: The async function to execute
            context: Context string for logging

        Returns:
            The result of the operation
        """
        attempt = 1

        while attempt <= config.max_retry_attempts:
            try:
                # Check rate limits before making request
                if self._is_rate_limited():
                    wait_time = self._calculate_wait_time()
                    logger.warning(
                        f"Rate limit active for {context}. Waiting {wait_time:.2f}s")
                    await self._delay(wait_time)

                # Record the request
                self._add_request()

                # Execute the operation
                return await operation()

            except Exception as error:
                if self._is_rate_limit_error(error) and attempt < config.max_retry_attempts:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"Rate limit hit for {context}. "
                        f"Attempt {attempt}/{config.max_retry_attempts}. "
                        f"Retrying in {delay:.2f}s"
                    )
                    await self._delay(delay)
                    attempt += 1
                    continue
                else:
                    # Re-raise the error if it's not a rate limit error or we've exhausted retries
                    raise error

        # This should never be reached, but just in case
        raise Exception(
            f"Max retry attempts ({config.max_retry_attempts}) exceeded for {context}")

    @asynccontextmanager
    async def rate_limited_operation(self, context: str = "API request"):
        """
        Context manager for rate-limited operations.

        Args:
            context: Context string for logging

        Yields:
            None
        """
        try:
            # Check rate limits before starting
            if self._is_rate_limited():
                wait_time = self._calculate_wait_time()
                logger.warning(
                    f"Rate limit active for {context}. Waiting {wait_time:.2f}s")
                await self._delay(wait_time)

            # Record the request
            self._add_request()

            yield

        except Exception as error:
            if self._is_rate_limit_error(error):
                logger.error(f"Rate limit error in {context}: {error}")
            raise error


def get_rate_limiter(
    api_type: str = "default",
    max_requests_per_second: Optional[int] = None
) -> RateLimiter:
    """
    Get a rate limiter instance for a specific API type.

    Args:
        api_type: Type of API (e.g., "market_data", "accounts", "products")
        max_requests_per_second: Custom per-second limit for this API type

    Returns:
        RateLimiter instance
    """
    if max_requests_per_second is None:
        if api_type == "market_data":
            max_requests_per_second = config.market_data_rate_limit
        elif api_type == "accounts":
            max_requests_per_second = config.accounts_rate_limit
        elif api_type == "products":
            max_requests_per_second = config.products_rate_limit
        else:
            max_requests_per_second = config.default_max_requests_per_second

    if api_type not in _rate_limiters:
        _rate_limiters[api_type] = RateLimiter(
            max_requests_per_second=max_requests_per_second
        )

    return _rate_limiters[api_type]


def rate_limited(
    api_type: str = "default",
    max_requests_per_second: Optional[int] = None
):
    """
    Decorator to apply rate limiting to async functions.

    Args:
        api_type: Type of API for rate limiting configuration
        max_requests_per_second: Custom per-second limit for this function

    Returns:
        Decorated function with rate limiting
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            rate_limiter = get_rate_limiter(
                api_type=api_type,
                max_requests_per_second=max_requests_per_second
            )

            async def operation():
                return await func(*args, **kwargs)

            context = f"{api_type} API call: {func.__name__}"
            return await rate_limiter.with_retry(operation, context)

        return wrapper
    return decorator


# Create config instance
config = RateLimitConfig()
