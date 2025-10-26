"""
Structured Logging Configuration.

JSON-formatted logs for production with correlation IDs.
"""

import logging
import sys
from typing import Any

import structlog
from pythonjsonlogger import jsonlogger

from src.core.config import get_settings

settings = get_settings()


def setup_logging() -> None:
    """
    Configure structured logging with structlog + python-json-logger.

    Logs include:
    - Timestamp
    - Log level
    - Message
    - Correlation ID
    - Additional context
    """
    # Configure standard library logging
    log_level = getattr(logging, settings.LOG_LEVEL)

    # Create JSON formatter
    if settings.LOG_FORMAT == "json":
        formatter = jsonlogger.JsonFormatter(
            fmt="%(timestamp)s %(level)s %(name)s %(message)s",
            rename_fields={
                "levelname": "level",
                "name": "logger",
                "asctime": "timestamp",
            },
        )
    else:
        # Human-readable format for development
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # Configure handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(log_level)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            # Render as JSON or KeyValue based on format
            structlog.processors.JSONRenderer()
            if settings.LOG_FORMAT == "json"
            else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Silence noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get structured logger.

    Usage:
        logger = get_logger(__name__)
        logger.info("workflow_created", workflow_id=workflow.id)

    Args:
        name: Logger name

    Returns:
        Structured logger
    """
    return structlog.get_logger(name)


class CorrelationIdProcessor:
    """
    Structlog processor to add correlation ID to logs.

    Reads correlation ID from contextvars.
    """

    def __call__(
        self,
        logger: Any,
        name: str,
        event_dict: dict[str, Any],
    ) -> dict[str, Any]:
        """Add correlation ID to log event."""
        # TODO: Get correlation ID from context
        # correlation_id = correlation_id_ctx.get(None)
        # if correlation_id:
        #     event_dict["correlation_id"] = correlation_id
        return event_dict

