"""
Utility functions for LLM operations with retry logic and error handling.
"""

import asyncio
import logging
from functools import wraps
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_with_exponential_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for retrying async functions with exponential backoff.

    Designed for LLM API calls that may fail due to:
    - Network timeouts
    - Rate limiting
    - Temporary server errors
    - Connection resets

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds before first retry (default: 1.0)
        max_delay: Maximum delay cap in seconds (default: 60.0)
        exponential_base: Base for exponential backoff (default: 2.0)
        exceptions: Tuple of exception types to catch and retry (default: all Exceptions)

    Returns:
        Decorated function with retry logic

    Example:
        ```python
        @retry_with_exponential_backoff(max_retries=3, initial_delay=2.0)
        async def call_gemini_api():
            return await llm.ainvoke(prompt)
        ```

    Backoff formula: delay = min(initial_delay * (exponential_base ** attempt), max_delay)
    - Attempt 0: 1.0s
    - Attempt 1: 2.0s
    - Attempt 2: 4.0s
    - Attempt 3: 8.0s (capped at max_delay)
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Exception | None = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:
                    last_exception = exc

                    if attempt == max_retries:
                        logger.error(
                            f"❌ {func.__name__} failed after {max_retries + 1} attempts. "
                            f"Last error: {type(exc).__name__}: {exc}"
                        )
                        raise

                    # Calculate exponential backoff delay
                    delay = min(
                        initial_delay * (exponential_base**attempt),
                        max_delay,
                    )

                    logger.warning(
                        f"⚠️ {func.__name__} attempt {attempt + 1}/{max_retries + 1} failed: "
                        f"{type(exc).__name__}: {exc}. Retrying in {delay:.1f}s..."
                    )

                    await asyncio.sleep(delay)

            # Should never reach here, but satisfy type checker
            if last_exception:
                raise last_exception
            raise RuntimeError(f"{func.__name__} failed without exception")

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            """Synchronous retry wrapper (not used for LLM calls, but included for completeness)"""
            import time

            last_exception: Exception | None = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)  # type: ignore
                except exceptions as exc:
                    last_exception = exc

                    if attempt == max_retries:
                        logger.error(
                            f"❌ {func.__name__} failed after {max_retries + 1} attempts. "
                            f"Last error: {type(exc).__name__}: {exc}"
                        )
                        raise

                    delay = min(
                        initial_delay * (exponential_base**attempt),
                        max_delay,
                    )

                    logger.warning(
                        f"⚠️ {func.__name__} attempt {attempt + 1}/{max_retries + 1} failed: "
                        f"{type(exc).__name__}: {exc}. Retrying in {delay:.1f}s..."
                    )

                    time.sleep(delay)

            if last_exception:
                raise last_exception
            raise RuntimeError(f"{func.__name__} failed without exception")

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator


# Common retry configurations for different LLM use cases

def retry_llm_call(func: Callable[..., T]) -> Callable[..., T]:
    """
    Standard retry configuration for LLM API calls.

    Configuration:
    - Max retries: 3
    - Initial delay: 2 seconds
    - Max delay: 30 seconds
    - Exponential base: 2

    Backoff sequence: 2s, 4s, 8s
    Total max time: ~14 seconds of waiting + execution time
    """
    return retry_with_exponential_backoff(
        max_retries=3,
        initial_delay=2.0,
        max_delay=30.0,
        exponential_base=2.0,
    )(func)


def retry_critical_llm_call(func: Callable[..., T]) -> Callable[..., T]:
    """
    Aggressive retry configuration for critical LLM operations.

    Use for:
    - Persona details generation (user-facing, expected to succeed)
    - Expensive operations (avoid re-running entire pipeline)

    Configuration:
    - Max retries: 5
    - Initial delay: 1 second
    - Max delay: 60 seconds
    - Exponential base: 2

    Backoff sequence: 1s, 2s, 4s, 8s, 16s
    Total max time: ~31 seconds of waiting + execution time
    """
    return retry_with_exponential_backoff(
        max_retries=5,
        initial_delay=1.0,
        max_delay=60.0,
        exponential_base=2.0,
    )(func)
