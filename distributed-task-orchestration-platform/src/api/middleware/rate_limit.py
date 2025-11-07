"""
Rate Limiting Middleware.

Protects API from being overwhelmed by too many requests.
Uses sliding window algorithm with Redis.
"""

import logging
import time
from typing import Callable

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.config import get_settings
from src.core.exceptions import RateLimitExceededError
from src.infrastructure.messaging.redis.client import get_redis

logger = logging.getLogger(__name__)
settings = get_settings()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using sliding window algorithm.

    Limits requests per IP address to prevent abuse.
    """

    def __init__(self, app: any) -> None:
        """Initialize middleware."""
        super().__init__(app)
        self.enabled = settings.RATE_LIMIT_ENABLED
        self.per_minute = settings.RATE_LIMIT_PER_MINUTE
        self.per_hour = settings.RATE_LIMIT_PER_HOUR

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Check rate limits before processing request.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response or rate limit error
        """
        if not self.enabled:
            return await call_next(request)

        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/api/v1/health"]:
            return await call_next(request)

        # Get client identifier (IP address)
        client_ip = self._get_client_ip(request)

        try:
            # Check rate limits
            await self._check_rate_limit(client_ip)

            # Process request
            response = await call_next(request)

            # Add rate limit headers
            response.headers["X-RateLimit-Limit-Minute"] = str(self.per_minute)
            response.headers["X-RateLimit-Limit-Hour"] = str(self.per_hour)

            # Get remaining from Redis
            remaining = await self._get_remaining(client_ip)
            response.headers["X-RateLimit-Remaining"] = str(remaining)

            return response

        except RateLimitExceededError as e:
            logger.warning(
                "Rate limit exceeded",
                extra={
                    "client_ip": client_ip,
                    "path": request.url.path,
                },
            )

            # Return 429 Too Many Requests
            return Response(
                content=str(e),
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={
                    "Retry-After": "60",  # Retry after 60 seconds
                    "X-RateLimit-Limit-Minute": str(self.per_minute),
                    "X-RateLimit-Remaining": "0",
                },
            )

    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address from request.

        Checks X-Forwarded-For header first (for load balancers).

        Args:
            request: Request object

        Returns:
            Client IP address
        """
        # Check X-Forwarded-For header (load balancer)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take first IP (client)
            return forwarded.split(",")[0].strip()

        # Fallback to direct connection
        if request.client:
            return request.client.host

        return "unknown"

    async def _check_rate_limit(self, client_ip: str) -> None:
        """
        Check if client exceeded rate limit.

        Uses sliding window algorithm with Redis.

        Args:
            client_ip: Client IP address

        Raises:
            RateLimitExceededError: If rate limit exceeded
        """
        redis = await get_redis()
        current_time = int(time.time())

        # Check per-minute limit
        minute_key = f"ratelimit:minute:{client_ip}:{current_time // 60}"
        minute_count = await redis.increment(minute_key)

        if minute_count == 1:
            # First request in this minute - set expiration
            await redis.expire(minute_key, 60)

        if minute_count > self.per_minute:
            raise RateLimitExceededError(
                f"Rate limit exceeded: {self.per_minute} requests per minute"
            )

        # Check per-hour limit
        hour_key = f"ratelimit:hour:{client_ip}:{current_time // 3600}"
        hour_count = await redis.increment(hour_key)

        if hour_count == 1:
            # First request in this hour - set expiration
            await redis.expire(hour_key, 3600)

        if hour_count > self.per_hour:
            raise RateLimitExceededError(
                f"Rate limit exceeded: {self.per_hour} requests per hour"
            )

    async def _get_remaining(self, client_ip: str) -> int:
        """
        Get remaining requests for client.

        Args:
            client_ip: Client IP address

        Returns:
            Remaining requests in current minute
        """
        redis = await get_redis()
        current_time = int(time.time())

        minute_key = f"ratelimit:minute:{client_ip}:{current_time // 60}"
        count = await redis.get(minute_key)

        if count is None:
            return self.per_minute

        return max(0, self.per_minute - int(count))

