"""
Retry logic with exponential backoff using tenacity.
Provides decorators for resilient API calls and operations.
"""

import logging
from functools import wraps
from typing import Callable, Type, Tuple, Any

from tenacity import (
    retry,
    retry_if_exception_type,
    retry_if_result,
    stop_after_attempt,
    stop_after_delay,
    wait_exponential,
    wait_random_exponential,
    before_log,
    after_log,
    retry_error_callback,
)

log = logging.getLogger(__name__)


def retry_with_backoff(
    max_attempts: int = 3,
    max_wait_seconds: int = 300,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry_callback: Callable = None,
):
    """
    Decorator for retrying operations with exponential backoff + jitter.
    
    Args:
        max_attempts: Maximum number of retry attempts
        max_wait_seconds: Maximum total wait time
        exceptions: Tuple of exceptions to catch and retry on
        on_retry_callback: Optional callback on retry
    """
    
    def error_callback(retry_state):
        log.error(
            f"Retries exhausted after {retry_state.attempt_number} attempts. "
            f"Last exception: {retry_state.outcome.exception()}"
        )
        if on_retry_callback:
            on_retry_callback(retry_state)
    
    return retry(
        retry=retry_if_exception_type(exceptions),
        stop=stop_after_attempt(max_attempts) | stop_after_delay(max_wait_seconds),
        wait=wait_random_exponential(multiplier=1, min=1, max=10),
        before=before_log(log, logging.DEBUG),
        after=after_log(log, logging.DEBUG),
        retry_error_callback=error_callback,
        reraise=True,
    )


def retry_on_false(
    max_attempts: int = 3,
    max_wait_seconds: int = 60,
):
    """
    Decorator that retries if function returns False.
    Useful for operations that return boolean success/failure.
    """
    return retry(
        retry=retry_if_result(lambda result: result is False),
        stop=stop_after_attempt(max_attempts) | stop_after_delay(max_wait_seconds),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        before=before_log(log, logging.DEBUG),
        after=after_log(log, logging.DEBUG),
        reraise=True,
    )


def idempotent_request(func: Callable) -> Callable:
    """
    Decorator marking a function as idempotent (safe to retry multiple times).
    Used for API calls and operations that can be safely retried.
    """
    func._is_idempotent = True
    return func


# Common retry patterns for specific operations

API_CALL_RETRY = retry_with_backoff(
    max_attempts=5,
    max_wait_seconds=120,
    exceptions=(ConnectionError, TimeoutError, OSError),
)

WEBHOOK_RETRY = retry_with_backoff(
    max_attempts=3,
    max_wait_seconds=60,
    exceptions=(ConnectionError, TimeoutError),
)

DATABASE_RETRY = retry_with_backoff(
    max_attempts=5,
    max_wait_seconds=30,
    exceptions=(Exception,),  # Catch all DB errors
)

INDEXING_RETRY = retry_with_backoff(
    max_attempts=3,
    max_wait_seconds=180,
    exceptions=(ConnectionError, TimeoutError),
)


# Utility function to wrap existing functions
def make_retryable(func: Callable, **retry_kwargs) -> Callable:
    """
    Convert any function to retryable with exponential backoff.
    
    Args:
        func: Function to wrap
        **retry_kwargs: Arguments passed to retry_with_backoff
        
    Returns:
        Wrapped function with retry logic
    """
    decorator = retry_with_backoff(**retry_kwargs)
    return decorator(func)
