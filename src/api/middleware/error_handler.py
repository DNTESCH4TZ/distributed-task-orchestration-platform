"""
Error Handler Middleware.

Catches exceptions and converts them to proper HTTP responses.
"""

import logging
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import ORJSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.exceptions import (
    APIException,
    ApplicationException,
    DomainException,
    InfrastructureException,
)

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle exceptions globally.

    Converts domain/infrastructure exceptions to HTTP responses.
    """

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Process request and handle exceptions.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response or error response
        """
        try:
            return await call_next(request)
        except APIException as exc:
            # API exceptions already have status code
            logger.warning(
                "API exception",
                extra={
                    "error": str(exc),
                    "code": exc.code,
                    "status_code": exc.status_code,
                    "correlation_id": getattr(request.state, "correlation_id", None),
                },
            )
            return ORJSONResponse(
                status_code=exc.status_code,
                content={
                    "error": exc.code,
                    "message": exc.message,
                    "correlation_id": getattr(request.state, "correlation_id", None),
                },
            )
        except DomainException as exc:
            # Domain exceptions = bad request (400)
            logger.warning(
                "Domain exception",
                extra={
                    "error": str(exc),
                    "code": exc.code,
                    "correlation_id": getattr(request.state, "correlation_id", None),
                },
            )
            return ORJSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": exc.code,
                    "message": exc.message,
                    "correlation_id": getattr(request.state, "correlation_id", None),
                },
            )
        except InfrastructureException as exc:
            # Infrastructure exceptions = service unavailable (503)
            logger.error(
                "Infrastructure exception",
                extra={
                    "error": str(exc),
                    "code": exc.code,
                    "correlation_id": getattr(request.state, "correlation_id", None),
                },
                exc_info=True,
            )
            return ORJSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "error": exc.code,
                    "message": exc.message,
                    "correlation_id": getattr(request.state, "correlation_id", None),
                },
            )
        except ApplicationException as exc:
            # Application exceptions = internal server error (500)
            logger.error(
                "Application exception",
                extra={
                    "error": str(exc),
                    "code": exc.code,
                    "correlation_id": getattr(request.state, "correlation_id", None),
                },
                exc_info=True,
            )
            return ORJSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": exc.code,
                    "message": exc.message,
                    "correlation_id": getattr(request.state, "correlation_id", None),
                },
            )
        except Exception as exc:
            # Unexpected exceptions = internal server error (500)
            logger.critical(
                "Unexpected exception",
                extra={
                    "error": str(exc),
                    "correlation_id": getattr(request.state, "correlation_id", None),
                },
                exc_info=True,
            )
            return ORJSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "InternalServerError",
                    "message": "An unexpected error occurred",
                    "correlation_id": getattr(request.state, "correlation_id", None),
                },
            )

