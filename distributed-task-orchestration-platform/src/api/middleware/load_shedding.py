"""
Load Shedding Middleware.

Rejects requests when system is overloaded to prevent cascade failures.
"""

import logging
import psutil
from typing import Callable

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoadSheddingMiddleware(BaseHTTPMiddleware):
    """
    Load shedding middleware based on system metrics.

    Rejects requests when:
    - CPU usage > threshold
    - Memory usage > threshold
    - Too many active requests
    """

    def __init__(
        self,
        app: any,
        cpu_threshold: float = 90.0,
        memory_threshold: float = 90.0,
        max_concurrent_requests: int = 1000,
    ) -> None:
        """
        Initialize middleware.

        Args:
            app: FastAPI app
            cpu_threshold: CPU usage percentage threshold
            memory_threshold: Memory usage percentage threshold
            max_concurrent_requests: Max concurrent requests
        """
        super().__init__(app)
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.max_concurrent_requests = max_concurrent_requests
        self._active_requests = 0

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Check system load before processing request.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response or 503 Service Unavailable
        """
        # Skip for health checks
        if request.url.path in ["/health", "/api/v1/health"]:
            return await call_next(request)

        # Check concurrent requests
        if self._active_requests >= self.max_concurrent_requests:
            logger.warning(
                "Load shedding: too many concurrent requests",
                extra={
                    "active_requests": self._active_requests,
                    "max": self.max_concurrent_requests,
                },
            )
            return self._create_overload_response("Too many concurrent requests")

        # Check CPU usage
        cpu_usage = psutil.cpu_percent(interval=0.1)
        if cpu_usage > self.cpu_threshold:
            logger.warning(
                "Load shedding: high CPU usage",
                extra={"cpu_usage": cpu_usage, "threshold": self.cpu_threshold},
            )
            return self._create_overload_response(f"High CPU usage: {cpu_usage:.1f}%")

        # Check memory usage
        memory = psutil.virtual_memory()
        if memory.percent > self.memory_threshold:
            logger.warning(
                "Load shedding: high memory usage",
                extra={"memory_usage": memory.percent, "threshold": self.memory_threshold},
            )
            return self._create_overload_response(
                f"High memory usage: {memory.percent:.1f}%"
            )

        # Process request
        self._active_requests += 1
        try:
            response = await call_next(request)
            return response
        finally:
            self._active_requests -= 1

    def _create_overload_response(self, reason: str) -> Response:
        """
        Create 503 Service Unavailable response.

        Args:
            reason: Reason for rejection

        Returns:
            503 response
        """
        return Response(
            content=f"Service temporarily overloaded: {reason}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            headers={
                "Retry-After": "30",  # Retry after 30 seconds
                "X-Load-Shedding": "true",
            },
        )

