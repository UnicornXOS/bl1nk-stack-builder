"""
Retry utilities for bl1nk-agent-builder
Implements retry logic with exponential backoff and jitter
"""

import asyncio
import logging
import random
import time
from typing import Callable, Any, Optional, Union, Dict, List
from functools import wraps
from enum import Enum

from app.config.settings import settings

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Retry strategies"""
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"


class RetryConfig:
    """Configuration for retry logic"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        jitter: bool = True,
        jitter_factor: float = 0.1,
        retryable_exceptions: Optional[List[type]] = None,
        non_retryable_exceptions: Optional[List[type]] = None
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.strategy = strategy
        self.jitter = jitter
        self.jitter_factor = jitter_factor
        self.retryable_exceptions = retryable_exceptions or [Exception]
        self.non_retryable_exceptions = non_retryable_exceptions or []
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """Determine if an exception should be retried"""
        
        # Check if this is a non-retryable exception
        for non_retryable in self.non_retryable_exceptions:
            if isinstance(exception, non_retryable):
                return False
        
        # Check if this is a retryable exception
        for retryable in self.retryable_exceptions:
            if isinstance(exception, retryable):
                return attempt < self.max_attempts
        
        # Default: retry all exceptions if not explicitly marked as non-retryable
        return attempt < self.max_attempts
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for the given attempt"""
        
        if self.strategy == RetryStrategy.FIXED:
            delay = self.base_delay
        
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.base_delay * attempt
        
        elif self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.base_delay * (2 ** (attempt - 1))
        
        else:
            delay = self.base_delay
        
        # Apply jitter if enabled
        if self.jitter:
            jitter_range = delay * self.jitter_factor
            delay += random.uniform(-jitter_range, jitter_range)
        
        # Ensure delay is positive
        delay = max(0.1, delay)
        
        # Cap at maximum delay
        return min(delay, self.max_delay)


class RetryResult:
    """Result of a retry operation"""
    
    def __init__(
        self,
        success: bool,
        result: Any = None,
        exception: Optional[Exception] = None,
        attempts: int = 0,
        total_delay: float = 0.0
    ):
        self.success = success
        self.result = result
        self.exception = exception
        self.attempts = attempts
        self.total_delay = total_delay


async def retry_async(
    func: Callable,
    *args,
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable] = None,
    **kwargs
) -> RetryResult:
    """
    Retry an async function with exponential backoff
    
    Args:
        func: Async function to retry
        *args: Positional arguments for the function
        config: Retry configuration
        on_retry: Callback function to call on each retry
        **kwargs: Keyword arguments for the function
    
    Returns:
        RetryResult with success status and result/exception
    """
    
    if config is None:
        config = RetryConfig()
    
    last_exception = None
    total_delay = 0.0
    attempts = 0
    
    for attempt in range(1, config.max_attempts + 1):
        attempts = attempt
        
        try:
            # Execute the function
            result = await func(*args, **kwargs)
            
            logger.debug(
                f"Function succeeded on attempt {attempt}",
                extra={
                    "event": "retry_success",
                    "function": func.__name__,
                    "attempt": attempt,
                    "attempts": attempts
                }
            )
            
            return RetryResult(
                success=True,
                result=result,
                attempts=attempt,
                total_delay=total_delay
            )
            
        except Exception as e:
            last_exception = e
            
            # Check if we should retry
            if not config.should_retry(e, attempt):
                logger.debug(
                    f"Function failed with non-retryable exception on attempt {attempt}",
                    extra={
                        "event": "retry_non_retryable",
                        "function": func.__name__,
                        "attempt": attempt,
                        "exception": str(e),
                        "exception_type": type(e).__name__
                    }
                )
                break
            
            # If this is the last attempt, don't delay
            if attempt == config.max_attempts:
                logger.debug(
                    f"Function failed on final attempt {attempt}",
                    extra={
                        "event": "retry_final_attempt",
                        "function": func.__name__,
                        "attempt": attempt,
                        "exception": str(e),
                        "exception_type": type(e).__name__
                    }
                )
                break
            
            # Calculate delay
            delay = config.calculate_delay(attempt)
            total_delay += delay
            
            # Log the retry
            logger.warning(
                f"Function failed on attempt {attempt}, retrying in {delay:.2f}s",
                extra={
                    "event": "retry_attempt",
                    "function": func.__name__,
                    "attempt": attempt,
                    "next_attempt": attempt + 1,
                    "delay": delay,
                    "exception": str(e),
                    "exception_type": type(e).__name__
                }
            )
            
            # Call retry callback if provided
            if on_retry:
                try:
                    await on_retry(attempt, e, delay)
                except Exception as callback_error:
                    logger.warning(
                        f"Retry callback failed: {callback_error}",
                        extra={
                            "event": "retry_callback_error",
                            "function": func.__name__,
                            "callback_error": str(callback_error)
                        }
                    )
            
            # Wait before retrying
            await asyncio.sleep(delay)
    
    # All attempts failed
    logger.error(
        f"Function failed after {attempts} attempts",
        extra={
            "event": "retry_exhausted",
            "function": func.__name__,
            "attempts": attempts,
            "total_delay": total_delay,
            "final_exception": str(last_exception),
            "exception_type": type(last_exception).__name__
        },
        exc_info=True
    )
    
    return RetryResult(
        success=False,
        exception=last_exception,
        attempts=attempts,
        total_delay=total_delay
    )


def retry_sync(
    func: Callable,
    *args,
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable] = None,
    **kwargs
) -> RetryResult:
    """
    Retry a sync function with exponential backoff
    
    Args:
        func: Sync function to retry
        *args: Positional arguments for the function
        config: Retry configuration
        on_retry: Callback function to call on each retry
        **kwargs: Keyword arguments for the function
    
    Returns:
        RetryResult with success status and result/exception
    """
    
    if config is None:
        config = RetryConfig()
    
    last_exception = None
    total_delay = 0.0
    attempts = 0
    
    for attempt in range(1, config.max_attempts + 1):
        attempts = attempt
        
        try:
            # Execute the function
            result = func(*args, **kwargs)
            
            logger.debug(
                f"Function succeeded on attempt {attempt}",
                extra={
                    "event": "retry_success",
                    "function": func.__name__,
                    "attempt": attempt,
                    "attempts": attempts
                }
            )
            
            return RetryResult(
                success=True,
                result=result,
                attempts=attempt,
                total_delay=total_delay
            )
            
        except Exception as e:
            last_exception = e
            
            # Check if we should retry
            if not config.should_retry(e, attempt):
                logger.debug(
                    f"Function failed with non-retryable exception on attempt {attempt}",
                    extra={
                        "event": "retry_non_retryable",
                        "function": func.__name__,
                        "attempt": attempt,
                        "exception": str(e),
                        "exception_type": type(e).__name__
                    }
                )
                break
            
            # If this is the last attempt, don't delay
            if attempt == config.max_attempts:
                logger.debug(
                    f"Function failed on final attempt {attempt}",
                    extra={
                        "event": "retry_final_attempt",
                        "function": func.__name__,
                        "attempt": attempt,
                        "exception": str(e),
                        "exception_type": type(e).__name__
                    }
                )
                break
            
            # Calculate delay
            delay = config.calculate_delay(attempt)
            total_delay += delay
            
            # Log the retry
            logger.warning(
                f"Function failed on attempt {attempt}, retrying in {delay:.2f}s",
                extra={
                    "event": "retry_attempt",
                    "function": func.__name__,
                    "attempt": attempt,
                    "next_attempt": attempt + 1,
                    "delay": delay,
                    "exception": str(e),
                    "exception_type": type(e).__name__
                }
            )
            
            # Call retry callback if provided
            if on_retry:
                try:
                    on_retry(attempt, e, delay)
                except Exception as callback_error:
                    logger.warning(
                        f"Retry callback failed: {callback_error}",
                        extra={
                            "event": "retry_callback_error",
                            "function": func.__name__,
                            "callback_error": str(callback_error)
                        }
                    )
            
            # Wait before retrying
            time.sleep(delay)
    
    # All attempts failed
    logger.error(
        f"Function failed after {attempts} attempts",
        extra={
            "event": "retry_exhausted",
            "function": func.__name__,
            "attempts": attempts,
            "total_delay": total_delay,
            "final_exception": str(last_exception),
            "exception_type": type(last_exception).__name__
        },
        exc_info=True
    )
    
    return RetryResult(
        success=False,
        exception=last_exception,
        attempts=attempts,
        total_delay=total_delay
    )


# Decorators for automatic retry
def retry_async_decorator(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    retryable_exceptions: Optional[List[type]] = None,
    non_retryable_exceptions: Optional[List[type]] = None,
    on_retry: Optional[Callable] = None
):
    """Decorator for automatic retry of async functions"""
    
    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        strategy=strategy,
        retryable_exceptions=retryable_exceptions,
        non_retryable_exceptions=non_retryable_exceptions
    )
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await retry_async(
                func, 
                *args, 
                config=config, 
                on_retry=on_retry,
                **kwargs
            )
            
            if not result.success:
                raise result.exception
            
            return result.result
        
        return wrapper
    
    return decorator


def retry_sync_decorator(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    retryable_exceptions: Optional[List[type]] = None,
    non_retryable_exceptions: Optional[List[type]] = None,
    on_retry: Optional[Callable] = None
):
    """Decorator for automatic retry of sync functions"""
    
    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        strategy=strategy,
        retryable_exceptions=retryable_exceptions,
        non_retryable_exceptions=non_retryable_exceptions
    )
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = retry_sync(
                func, 
                *args, 
                config=config, 
                on_retry=on_retry,
                **kwargs
            )
            
            if not result.success:
                raise result.exception
            
            return result.result
        
        return wrapper
    
    return decorator


# Predefined retry configurations for common use cases
RETRY_CONFIGS = {
    "database": RetryConfig(
        max_attempts=5,
        base_delay=1.0,
        max_delay=30.0,
        strategy=RetryStrategy.EXPONENTIAL,
        retryable_exceptions=[Exception],  # Retry most database errors
        non_retryable_exceptions=[Exception]  # You can be more specific here
    ),
    
    "api_call": RetryConfig(
        max_attempts=3,
        base_delay=2.0,
        max_delay=60.0,
        strategy=RetryStrategy.EXPONENTIAL,
        retryable_exceptions=[Exception],  # Retry API call failures
        non_retryable_exceptions=[Exception]  # You can specify specific HTTP errors
    ),
    
    "quick_retry": RetryConfig(
        max_attempts=2,
        base_delay=0.5,
        max_delay=5.0,
        strategy=RetryStrategy.FIXED,
        retryable_exceptions=[Exception]
    ),
    
    "long_retry": RetryConfig(
        max_attempts=10,
        base_delay=5.0,
        max_delay=300.0,  # 5 minutes
        strategy=RetryStrategy.EXPONENTIAL,
        retryable_exceptions=[Exception]
    )
}


# Convenience functions
async def retry_database_operation(func: Callable, *args, **kwargs) -> Any:
    """Retry a database operation"""
    
    result = await retry_async(func, *args, config=RETRY_CONFIGS["database"], **kwargs)
    
    if not result.success:
        raise result.exception
    
    return result.result


async def retry_api_call(func: Callable, *args, **kwargs) -> Any:
    """Retry an API call"""
    
    result = await retry_async(func, *args, config=RETRY_CONFIGS["api_call"], **kwargs)
    
    if not result.success:
        raise result.exception
    
    return result.result


# Retry callback functions
async def log_retry_attempt(attempt: int, exception: Exception, delay: float):
    """Log retry attempt details"""
    
    logger.info(
        f"Retry attempt {attempt} after {delay:.2f}s delay",
        extra={
            "event": "retry_log",
            "attempt": attempt,
            "delay": delay,
            "exception": str(exception),
            "exception_type": type(exception).__name__
        }
    )


async def exponential_backoff_retry(attempt: int, exception: Exception, delay: float):
    """Retry with exponential backoff and circuit breaker pattern"""
    
    # You could implement circuit breaker logic here
    # For now, just log the retry
    await log_retry_attempt(attempt, exception, delay)