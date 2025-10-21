"""
Correlation ID Middleware.

Adds unique correlation ID to each request for distributed tracing.
"""

import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

CORRELATION_ID_HEADER = "X-Correlation-ID"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add correlation ID to requests.

    The correlation ID is:
    1. Read from X-Correlation-ID header if present
    2. Generated as new UUID if not present
    3. Added to response headers
    4. Available in request.state for logging
    """

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Process request and add correlation ID.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response with correlation ID header
        """
        # Get or generate correlation ID
        correlation_id = request.headers.get(
            CORRELATION_ID_HEADER, str(uuid.uuid4())
        )

        # Store in request state for logging
        request.state.correlation_id = correlation_id

        # Process request
        response = await call_next(request)

        # Add to response headers
        response.headers[CORRELATION_ID_HEADER] = correlation_id

        return response

