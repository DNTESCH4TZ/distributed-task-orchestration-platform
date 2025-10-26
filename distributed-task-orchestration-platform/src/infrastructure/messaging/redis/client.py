"""
Redis Client with Connection Pooling.

High-performance async Redis client using hiredis for C-level performance.
"""

import logging
from typing import Any

import orjson
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

from src.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RedisClient:
    """
    Async Redis client with connection pooling.

    Features:
    - Connection pooling для 1M RPS
    - hiredis parser (C-level performance)
    - orjson serialization (2-5x faster)
    - Health checking
    """

    def __init__(self) -> None:
        """Initialize Redis client."""
        self._pool: ConnectionPool | None = None
        self._client: redis.Redis | None = None

    async def connect(self) -> None:
        """
        Create connection pool and client.

        Uses hiredis parser for performance.
        """
        self._pool = ConnectionPool.from_url(
            str(settings.REDIS_URL),
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            socket_keepalive=settings.REDIS_SOCKET_KEEPALIVE,
            socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
            health_check_interval=settings.REDIS_HEALTH_CHECK_INTERVAL,
            decode_responses=False,  # Work with bytes for performance
        )

        self._client = redis.Redis(connection_pool=self._pool)

        # Test connection
        await self._client.ping()
        logger.info(
            "Redis connected",
            extra={
                "url": str(settings.REDIS_URL),
                "max_connections": settings.REDIS_MAX_CONNECTIONS,
            },
        )

    async def close(self) -> None:
        """Close connection pool."""
        if self._client:
            await self._client.close()
        if self._pool:
            await self._pool.disconnect()
        logger.info("Redis connection closed")

    async def get(self, key: str) -> Any | None:
        """
        Get value from Redis.

        Args:
            key: Cache key

        Returns:
            Deserialized value or None if not found
        """
        if self._client is None:
            raise RuntimeError("Redis not connected")

        value = await self._client.get(key)
        if value is None:
            return None

        # Deserialize with orjson (faster than json)
        return orjson.loads(value)

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """
        Set value in Redis.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None = no expiration)

        Returns:
            True if successful
        """
        if self._client is None:
            raise RuntimeError("Redis not connected")

        # Serialize with orjson (faster than json)
        serialized = orjson.dumps(value)

        if ttl is not None:
            return await self._client.setex(key, ttl, serialized)
        else:
            return await self._client.set(key, serialized)

    async def delete(self, key: str) -> int:
        """
        Delete key from Redis.

        Args:
            key: Cache key

        Returns:
            Number of keys deleted
        """
        if self._client is None:
            raise RuntimeError("Redis not connected")

        return await self._client.delete(key)

    async def exists(self, key: str) -> bool:
        """
        Check if key exists.

        Args:
            key: Cache key

        Returns:
            True if exists
        """
        if self._client is None:
            raise RuntimeError("Redis not connected")

        return bool(await self._client.exists(key))

    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment counter.

        Args:
            key: Counter key
            amount: Amount to increment

        Returns:
            New value
        """
        if self._client is None:
            raise RuntimeError("Redis not connected")

        return await self._client.incrby(key, amount)

    async def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration on key.

        Args:
            key: Cache key
            ttl: Time to live in seconds

        Returns:
            True if successful
        """
        if self._client is None:
            raise RuntimeError("Redis not connected")

        return await self._client.expire(key, ttl)

    async def get_many(self, keys: list[str]) -> list[Any | None]:
        """
        Get multiple values (batch operation).

        Args:
            keys: List of cache keys

        Returns:
            List of deserialized values
        """
        if self._client is None:
            raise RuntimeError("Redis not connected")

        values = await self._client.mget(keys)
        return [orjson.loads(v) if v is not None else None for v in values]

    async def set_many(
        self,
        mapping: dict[str, Any],
        ttl: int | None = None,
    ) -> bool:
        """
        Set multiple values (batch operation).

        Args:
            mapping: Dict of key-value pairs
            ttl: Time to live in seconds

        Returns:
            True if successful
        """
        if self._client is None:
            raise RuntimeError("Redis not connected")

        # Serialize all values
        serialized = {k: orjson.dumps(v) for k, v in mapping.items()}

        # Use pipeline for atomic operation
        async with self._client.pipeline() as pipe:
            await pipe.mset(serialized)
            if ttl is not None:
                for key in serialized:
                    await pipe.expire(key, ttl)
            await pipe.execute()

        return True

    async def health_check(self) -> bool:
        """
        Check Redis health.

        Returns:
            True if healthy
        """
        if self._client is None:
            return False

        try:
            await self._client.ping()
            return True
        except Exception:
            return False


# Global Redis client instance
_redis_client: RedisClient | None = None


async def get_redis() -> RedisClient:
    """
    Get Redis client instance.

    Returns:
        Redis client
    """
    global _redis_client

    if _redis_client is None:
        _redis_client = RedisClient()
        await _redis_client.connect()

    return _redis_client


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis_client

    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None

