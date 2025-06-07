import asyncio
import logging
from functools import wraps
from typing import Callable, Any, Coroutine

logger = logging.getLogger(__name__)

# Type alias for an async function that can be retried
AsyncRetryableFunc = Callable[..., Coroutine[Any, Any, Any]]

def retry_async_function(
    retries: int = 3,
    delay_seconds: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,) # Tuple of exception types to catch and retry on
) -> Callable[[AsyncRetryableFunc], AsyncRetryableFunc]:
    """
    A decorator for retrying an async function with exponential backoff.

    :param retries: Maximum number of retries.
    :param delay_seconds: Initial delay between retries.
    :param backoff_factor: Factor by which the delay increases after each retry.
    :param exceptions: A tuple of Exception classes to catch and retry on.
    """
    def decorator(func: AsyncRetryableFunc) -> AsyncRetryableFunc:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay_seconds
            for attempt in range(retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == retries:
                        logger.error(
                            f"Function {func.__name__} failed after {retries + 1} attempts. Last error: {e}"
                        )
                        raise # Re-raise the last exception

                    logger.warning(
                        f"Attempt {attempt + 1}/{retries + 1} failed for {func.__name__} with error: {e}. "
                        f"Retrying in {current_delay:.2f} seconds..."
                    )
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff_factor
        return wrapper
    return decorator
