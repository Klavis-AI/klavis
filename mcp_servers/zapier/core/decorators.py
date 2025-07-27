"""
Decorators for Zapier MCP Server.

This module contains decorators that implement cross-cutting concerns
like retry, caching, validation, and logging using the Decorator pattern.
"""

import functools
import logging
import asyncio
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from datetime import datetime
import json

from .exceptions import ValidationError, ServiceError

T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Retry decorator for automatic retry on failure.
    
    Implements exponential backoff retry logic for failed operations.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay on each retry
        exceptions: Tuple of exceptions to catch and retry
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logging.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay} seconds..."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logging.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {e}"
                        )
            
            raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logging.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay} seconds..."
                        )
                        import time
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logging.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {e}"
                        )
            
            raise last_exception
        
        # Return async wrapper if function is async, sync wrapper otherwise
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def cache(
    ttl: Optional[int] = 300,
    key_func: Optional[Callable] = None,
    cache_instance: Optional[Any] = None
):
    """
    Cache decorator for function result caching.
    
    Implements caching logic with TTL and custom key generation.
    
    Args:
        ttl: Time to live for cached results in seconds
        key_func: Function to generate cache keys
        cache_instance: Cache instance to use
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            if cache_instance:
                try:
                    cached_result = await cache_instance.get(cache_key)
                    if cached_result is not None:
                        logging.debug(f"Cache hit for {func.__name__}")
                        return cached_result
                except Exception as e:
                    logging.warning(f"Cache get failed: {e}")
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            if cache_instance:
                try:
                    await cache_instance.set(cache_key, result, ttl)
                    logging.debug(f"Cached result for {func.__name__}")
                except Exception as e:
                    logging.warning(f"Cache set failed: {e}")
            
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            if cache_instance:
                try:
                    cached_result = cache_instance.get(cache_key)
                    if cached_result is not None:
                        logging.debug(f"Cache hit for {func.__name__}")
                        return cached_result
                except Exception as e:
                    logging.warning(f"Cache get failed: {e}")
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            if cache_instance:
                try:
                    cache_instance.set(cache_key, result, ttl)
                    logging.debug(f"Cached result for {func.__name__}")
                except Exception as e:
                    logging.warning(f"Cache set failed: {e}")
            
            return result
        
        # Return async wrapper if function is async, sync wrapper otherwise
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def validate(validator: Optional[Callable] = None, schema: Optional[Dict] = None):
    """
    Validation decorator for input validation.
    
    Implements validation logic with custom validators or schemas.
    
    Args:
        validator: Custom validation function
        schema: Validation schema
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Validate inputs
            if validator:
                if not validator(*args, **kwargs):
                    raise ValidationError(f"Validation failed for {func.__name__}")
            elif schema:
                # Basic schema validation
                for key, rules in schema.items():
                    if key in kwargs:
                        value = kwargs[key]
                        if 'required' in rules and rules['required'] and value is None:
                            raise ValidationError(f"Required field '{key}' is missing")
                        if 'type' in rules and not isinstance(value, rules['type']):
                            raise ValidationError(f"Field '{key}' must be of type {rules['type']}")
                        if 'min_length' in rules and len(str(value)) < rules['min_length']:
                            raise ValidationError(f"Field '{key}' is too short")
                        if 'max_length' in rules and len(str(value)) > rules['max_length']:
                            raise ValidationError(f"Field '{key}' is too long")
            
            return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Validate inputs
            if validator:
                if not validator(*args, **kwargs):
                    raise ValidationError(f"Validation failed for {func.__name__}")
            elif schema:
                # Basic schema validation
                for key, rules in schema.items():
                    if key in kwargs:
                        value = kwargs[key]
                        if 'required' in rules and rules['required'] and value is None:
                            raise ValidationError(f"Required field '{key}' is missing")
                        if 'type' in rules and not isinstance(value, rules['type']):
                            raise ValidationError(f"Field '{key}' must be of type {rules['type']}")
                        if 'min_length' in rules and len(str(value)) < rules['min_length']:
                            raise ValidationError(f"Field '{key}' is too short")
                        if 'max_length' in rules and len(str(value)) > rules['max_length']:
                            raise ValidationError(f"Field '{key}' is too long")
            
            return func(*args, **kwargs)
        
        # Return async wrapper if function is async, sync wrapper otherwise
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def log_operation(
    level: str = "INFO",
    include_args: bool = True,
    include_result: bool = False,
    include_timing: bool = True
):
    """
    Logging decorator for operation logging.
    
    Implements comprehensive logging for function calls with timing and results.
    
    Args:
        level: Logging level
        include_args: Whether to log function arguments
        include_result: Whether to log function results
        include_timing: Whether to log execution time
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            logger = logging.getLogger(func.__module__)
            
            # Log function call
            log_message = f"Calling {func.__name__}"
            if include_args:
                log_message += f" with args={args}, kwargs={kwargs}"
            
            getattr(logger, level.lower())(log_message)
            
            try:
                result = await func(*args, **kwargs)
                
                # Log success
                log_message = f"Completed {func.__name__}"
                if include_timing:
                    execution_time = (datetime.utcnow() - start_time).total_seconds()
                    log_message += f" in {execution_time:.3f}s"
                if include_result:
                    log_message += f" with result={result}"
                
                getattr(logger, level.lower())(log_message)
                return result
                
            except Exception as e:
                # Log error
                log_message = f"Failed {func.__name__}"
                if include_timing:
                    execution_time = (datetime.utcnow() - start_time).total_seconds()
                    log_message += f" after {execution_time:.3f}s"
                log_message += f" with error: {e}"
                
                getattr(logger, "ERROR")(log_message)
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            logger = logging.getLogger(func.__module__)
            
            # Log function call
            log_message = f"Calling {func.__name__}"
            if include_args:
                log_message += f" with args={args}, kwargs={kwargs}"
            
            getattr(logger, level.lower())(log_message)
            
            try:
                result = func(*args, **kwargs)
                
                # Log success
                log_message = f"Completed {func.__name__}"
                if include_timing:
                    execution_time = (datetime.utcnow() - start_time).total_seconds()
                    log_message += f" in {execution_time:.3f}s"
                if include_result:
                    log_message += f" with result={result}"
                
                getattr(logger, level.lower())(log_message)
                return result
                
            except Exception as e:
                # Log error
                log_message = f"Failed {func.__name__}"
                if include_timing:
                    execution_time = (datetime.utcnow() - start_time).total_seconds()
                    log_message += f" after {execution_time:.3f}s"
                log_message += f" with error: {e}"
                
                getattr(logger, "ERROR")(log_message)
                raise
        
        # Return async wrapper if function is async, sync wrapper otherwise
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def rate_limit(
    max_calls: int = 100,
    time_window: int = 60,
    storage: Optional[Dict] = None
):
    """
    Rate limiting decorator.
    
    Implements rate limiting logic to prevent API abuse.
    
    Args:
        max_calls: Maximum number of calls allowed
        time_window: Time window in seconds
        storage: Storage for rate limiting data
    """
    if storage is None:
        storage = {}
    
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            current_time = datetime.utcnow()
            key = f"{func.__name__}:{current_time.timestamp() // time_window}"
            
            # Check rate limit
            if key in storage:
                calls = storage[key]
                if calls >= max_calls:
                    raise ServiceError(f"Rate limit exceeded for {func.__name__}")
                storage[key] = calls + 1
            else:
                storage[key] = 1
            
            return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            current_time = datetime.utcnow()
            key = f"{func.__name__}:{current_time.timestamp() // time_window}"
            
            # Check rate limit
            if key in storage:
                calls = storage[key]
                if calls >= max_calls:
                    raise ServiceError(f"Rate limit exceeded for {func.__name__}")
                storage[key] = calls + 1
            else:
                storage[key] = 1
            
            return func(*args, **kwargs)
        
        # Return async wrapper if function is async, sync wrapper otherwise
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    expected_exception: type = Exception
):
    """
    Circuit breaker decorator.
    
    Implements circuit breaker pattern to prevent cascading failures.
    
    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Time to wait before attempting recovery
        expected_exception: Exception type to monitor
    """
    def decorator(func: F) -> F:
        # Circuit breaker state
        failure_count = 0
        last_failure_time = None
        circuit_open = False
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            nonlocal failure_count, last_failure_time, circuit_open
            
            # Check if circuit is open
            if circuit_open:
                if (datetime.utcnow() - last_failure_time).total_seconds() < recovery_timeout:
                    raise ServiceError(f"Circuit breaker is open for {func.__name__}")
                else:
                    # Try to close circuit
                    circuit_open = False
                    failure_count = 0
            
            try:
                result = await func(*args, **kwargs)
                # Reset failure count on success
                failure_count = 0
                return result
            except expected_exception as e:
                failure_count += 1
                last_failure_time = datetime.utcnow()
                
                if failure_count >= failure_threshold:
                    circuit_open = True
                    logging.error(f"Circuit breaker opened for {func.__name__}")
                
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            nonlocal failure_count, last_failure_time, circuit_open
            
            # Check if circuit is open
            if circuit_open:
                if (datetime.utcnow() - last_failure_time).total_seconds() < recovery_timeout:
                    raise ServiceError(f"Circuit breaker is open for {func.__name__}")
                else:
                    # Try to close circuit
                    circuit_open = False
                    failure_count = 0
            
            try:
                result = func(*args, **kwargs)
                # Reset failure count on success
                failure_count = 0
                return result
            except expected_exception as e:
                failure_count += 1
                last_failure_time = datetime.utcnow()
                
                if failure_count >= failure_threshold:
                    circuit_open = True
                    logging.error(f"Circuit breaker opened for {func.__name__}")
                
                raise
        
        # Return async wrapper if function is async, sync wrapper otherwise
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator 