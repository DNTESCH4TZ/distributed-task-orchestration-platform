"""
Cache Decorators and Utilities.

Provides decorators for caching function results in Redis.
"""

import functools
import hashlib
import logging
from typing import Any, Callable, TypeVar

import orjson

from src.infrastructure.messaging.redis.client import get_redis

logger = logging.getLogger(__name__)

T = TypeVar("T")


def cache_key(*args: Any, **kwargs: Any) -> str:
    """
    Generate cache key from function arguments.

    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Cache key hash
    """
    # Serialize arguments
    key_data = orjson.dumps({"args": args, "kwargs": kwargs})

    # Hash for consistent key length
    return hashlib.sha256(key_data).hexdigest()


def cached(
    ttl: int = 60,
    prefix: str = "cache",
    key_func: Callable[..., str] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Cache decorator for async functions.

    Usage:
        @cached(ttl=300, prefix="workflow")
        async def get_workflow(workflow_id: UUID) -> Workflow:
            ...

    Args:
        ttl: Time to live in seconds
        prefix: Key prefix for namespacing
        key_func: Custom key generation function

    Returns:
        Decorated function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            redis = await get_redis()

            # Generate cache key
            if key_func is not None:
                key_suffix = key_func(*args, **kwargs)
            else:
                key_suffix = cache_key(*args, **kwargs)

            cache_key_full = f"{prefix}:{func.__name__}:{key_suffix}"

            # Try to get from cache
            cached_value = await redis.get(cache_key_full)
            if cached_value is not None:
                logger.debug(
                    "Cache hit",
                    extra={
                        "function": func.__name__,
                        "key": cache_key_full,
                    },
                )
                return cached_value

            # Cache miss - call function
            logger.debug(
                "Cache miss",
                extra={
                    "function": func.__name__,
                    "key": cache_key_full,
                },
            )
            result = await func(*args, **kwargs)

            # Store in cache
            await redis.set(cache_key_full, result, ttl=ttl)

            return result

        return wrapper

    return decorator


def invalidate_cache(
    prefix: str,
    key_func: Callable[..., str] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Invalidate cache decorator.

    Usage:
        @invalidate_cache(prefix="workflow")
        async def update_workflow(workflow_id: UUID) -> None:
            ...

    Args:
        prefix: Key prefix to invalidate
        key_func: Custom key generation function

    Returns:
        Decorated function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            # Call original function
            result = await func(*args, **kwargs)

            # Invalidate cache
            redis = await get_redis()

            if key_func is not None:
                key_suffix = key_func(*args, **kwargs)
            else:
                key_suffix = cache_key(*args, **kwargs)

            cache_key_full = f"{prefix}:{func.__name__}:{key_suffix}"
            await redis.delete(cache_key_full)

            logger.debug(
                "Cache invalidated",
                extra={
                    "function": func.__name__,
                    "key": cache_key_full,
                },
            )

            return result

        return wrapper

    return decorator


class CacheManager:
    """Cache management utilities."""

    @staticmethod
    async def clear_prefix(prefix: str) -> int:
        """
        Clear all keys with given prefix.

        Args:
            prefix: Key prefix

        Returns:
            Number of keys deleted
        """
        redis = await get_redis()
        # Note: In production, use SCAN instead of KEYS for large datasets
        # This is a simplified version
        count = 0
        # TODO: Implement proper SCAN-based deletion
        logger.warning(
            "Prefix deletion not fully implemented",
            extra={"prefix": prefix},
        )
        return count

    @staticmethod
    async def get_stats() -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Cache stats dict
        """
        redis = await get_redis()
        # TODO: Implement proper stats collection
        return {
            "hits": 0,
            "misses": 0,
            "hit_rate": 0.0,
        }

