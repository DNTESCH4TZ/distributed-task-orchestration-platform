"""
Custom exceptions for the application.

All exceptions inherit from base ApplicationException for easy catching.
"""


class ApplicationException(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, code: str | None = None) -> None:
        self.message = message
        self.code = code or self.__class__.__name__
        super().__init__(self.message)


# ========================================
# Domain Exceptions
# ========================================


class DomainException(ApplicationException):
    """Base exception for domain layer errors."""


class EntityNotFoundError(DomainException):
    """Entity not found in repository."""


class EntityAlreadyExistsError(DomainException):
    """Entity with same identifier already exists."""


class InvalidEntityStateError(DomainException):
    """Entity is in invalid state for requested operation."""


class WorkflowValidationError(DomainException):
    """Workflow definition is invalid."""


class TaskValidationError(DomainException):
    """Task definition is invalid."""


class CircularDependencyError(DomainException):
    """Circular dependency detected in workflow DAG."""


class MaxDepthExceededError(DomainException):
    """Maximum workflow nesting depth exceeded."""


class MaxRetryExceededError(DomainException):
    """Maximum retry attempts exceeded."""


# ========================================
# Infrastructure Exceptions
# ========================================


class InfrastructureException(ApplicationException):
    """Base exception for infrastructure layer errors."""


class DatabaseError(InfrastructureException):
    """Database operation failed."""


class RedisError(InfrastructureException):
    """Redis operation failed."""


class MessageQueueError(InfrastructureException):
    """Message queue operation failed."""


class CircuitBreakerOpenError(InfrastructureException):
    """Circuit breaker is open, request rejected."""


class ExternalServiceError(InfrastructureException):
    """External service call failed."""


# ========================================
# Application Exceptions
# ========================================


class ApplicationLayerException(ApplicationException):
    """Base exception for application layer errors."""


class WorkflowExecutionError(ApplicationLayerException):
    """Workflow execution failed."""


class TaskExecutionError(ApplicationLayerException):
    """Task execution failed."""


class CompensationError(ApplicationLayerException):
    """Saga compensation failed."""


class TimeoutError(ApplicationLayerException):
    """Operation exceeded timeout."""


# ========================================
# API Exceptions
# ========================================


class APIException(ApplicationException):
    """Base exception for API layer errors."""

    def __init__(
        self, message: str, status_code: int = 500, code: str | None = None
    ) -> None:
        super().__init__(message, code)
        self.status_code = status_code


class BadRequestError(APIException):
    """Bad request (400)."""

    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message, status_code=400, code=code)


class UnauthorizedError(APIException):
    """Unauthorized (401)."""

    def __init__(self, message: str = "Unauthorized", code: str | None = None) -> None:
        super().__init__(message, status_code=401, code=code)


class ForbiddenError(APIException):
    """Forbidden (403)."""

    def __init__(
        self, message: str = "Forbidden", code: str | None = None
    ) -> None:
        super().__init__(message, status_code=403, code=code)


class NotFoundError(APIException):
    """Not found (404)."""

    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message, status_code=404, code=code)


class ConflictError(APIException):
    """Conflict (409)."""

    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message, status_code=409, code=code)


class RateLimitExceededError(APIException):
    """Rate limit exceeded (429)."""

    def __init__(
        self, message: str = "Rate limit exceeded", code: str | None = None
    ) -> None:
        super().__init__(message, status_code=429, code=code)


class InternalServerError(APIException):
    """Internal server error (500)."""

    def __init__(
        self, message: str = "Internal server error", code: str | None = None
    ) -> None:
        super().__init__(message, status_code=500, code=code)


class ServiceUnavailableError(APIException):
    """Service unavailable (503)."""

    def __init__(
        self, message: str = "Service temporarily unavailable", code: str | None = None
    ) -> None:
        super().__init__(message, status_code=503, code=code)

