"""
Request Timeout Middleware.

Prevents requests from running indefinitely.
"""

import asyncio
import logging
from typing import Callable

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TimeoutMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce request timeouts.

    Prevents slow requests from consuming resources.
    """

    def __init__(self, app: any, timeout: int | None = None) -> None:
        """
        Initialize middleware.

        Args:
            app: FastAPI app
            timeout: Request timeout in seconds
        """
        super().__init__(app)
        self.timeout = timeout or settings.REQUEST_TIMEOUT

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Process request with timeout.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response or timeout error
        """
        try:
            # Execute with timeout
            response = await asyncio.wait_for(
                call_next(request),
                timeout=self.timeout,
            )
            return response

        except asyncio.TimeoutError:
            logger.error(
                "Request timeout",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "timeout": self.timeout,
                },
            )

            return Response(
                content=f"Request timeout after {self.timeout} seconds",
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                headers={
                    "X-Timeout": str(self.timeout),
                },
            )

