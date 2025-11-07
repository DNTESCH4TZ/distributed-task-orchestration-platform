"""
Circuit Breaker Pattern Implementation.

Protects system from cascading failures when calling external services.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, TypeVar

from src.core.exceptions import CircuitBreakerOpenError

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Async circuit breaker for external service calls.

    Prevents cascading failures by:
    1. Tracking failures
    2. Opening circuit after threshold
    3. Rejecting requests when open
    4. Testing recovery periodically

    Usage:
        breaker = CircuitBreaker(
            failure_threshold=5,
            timeout=60,
            expected_exception=httpx.HTTPError,
        )

        @breaker
        async def call_external_api():
            async with httpx.AsyncClient() as client:
                return await client.get("https://api.example.com")
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        expected_exception: type[Exception] = Exception,
        name: str | None = None,
    ) -> None:
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to wait before attempting recovery (half-open)
            expected_exception: Exception type that counts as failure
            name: Circuit breaker name for logging
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.name = name or "circuit_breaker"

        # State
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: datetime | None = None
        self._success_count = 0

        # Stats
        self._total_calls = 0
        self._total_failures = 0
        self._total_rejections = 0

        logger.info(
            "Circuit breaker initialized",
            extra={
                "name": self.name,
                "failure_threshold": failure_threshold,
                "timeout": timeout,
            },
        )

    @property
    def state(self) -> CircuitState:
        """Get current state."""
        return self._state

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self._state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (rejecting requests)."""
        return self._state == CircuitState.OPEN

    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open (testing recovery)."""
        return self._state == CircuitState.HALF_OPEN

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        Decorator for protecting async functions.

        Args:
            func: Async function to protect

        Returns:
            Wrapped function
        """
        import functools

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            return await self.call(func, *args, **kwargs)

        return wrapper

    async def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        self._total_calls += 1

        # Check if we should attempt recovery
        if self._should_attempt_reset():
            self._state = CircuitState.HALF_OPEN
            logger.info(
                "Circuit breaker attempting recovery",
                extra={"name": self.name},
            )

        # Reject request if circuit is open
        if self.is_open:
            self._total_rejections += 1
            logger.warning(
                "Circuit breaker open, request rejected",
                extra={
                    "name": self.name,
                    "failure_count": self._failure_count,
                    "last_failure": self._last_failure_time,
                },
            )
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is open. "
                f"Service unavailable due to {self._failure_count} consecutive failures."
            )

        try:
            # Call function
            result = await func(*args, **kwargs)

            # Success - update state
            self._on_success()

            return result

        except self.expected_exception as e:
            # Expected failure - update state
            self._on_failure()
            raise

        except Exception as e:
            # Unexpected exception - pass through without affecting circuit
            logger.error(
                "Unexpected exception in circuit breaker",
                extra={
                    "name": self.name,
                    "exception": str(e),
                },
                exc_info=True,
            )
            raise

    def _on_success(self) -> None:
        """Handle successful call."""
        self._failure_count = 0
        self._success_count += 1

        if self.is_half_open:
            # Recovered - close circuit
            logger.info(
                "Circuit breaker recovered, closing circuit",
                extra={"name": self.name},
            )
            self._state = CircuitState.CLOSED
            self._success_count = 0

    def _on_failure(self) -> None:
        """Handle failed call."""
        self._failure_count += 1
        self._total_failures += 1
        self._last_failure_time = datetime.utcnow()

        logger.warning(
            "Circuit breaker recorded failure",
            extra={
                "name": self.name,
                "failure_count": self._failure_count,
                "threshold": self.failure_threshold,
            },
        )

        # Open circuit if threshold exceeded
        if self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
            logger.error(
                "Circuit breaker opened due to failures",
                extra={
                    "name": self.name,
                    "failure_count": self._failure_count,
                    "timeout": self.timeout,
                },
            )

        # If already half-open, go back to open
        if self.is_half_open:
            self._state = CircuitState.OPEN
            logger.warning(
                "Circuit breaker recovery failed, reopening",
                extra={"name": self.name},
            )

    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset circuit."""
        if not self.is_open:
            return False

        if self._last_failure_time is None:
            return False

        # Check if timeout has passed
        elapsed = datetime.utcnow() - self._last_failure_time
        return elapsed >= timedelta(seconds=self.timeout)

    def reset(self) -> None:
        """Manually reset circuit breaker."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None

        logger.info("Circuit breaker manually reset", extra={"name": self.name})

    def get_stats(self) -> dict[str, Any]:
        """
        Get circuit breaker statistics.

        Returns:
            Statistics dict
        """
        return {
            "name": self.name,
            "state": self._state.value,
            "total_calls": self._total_calls,
            "total_failures": self._total_failures,
            "total_rejections": self._total_rejections,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure_time": (
                self._last_failure_time.isoformat() if self._last_failure_time else None
            ),
        }


# Global circuit breakers registry
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    timeout: int = 60,
    expected_exception: type[Exception] = Exception,
) -> CircuitBreaker:
    """
    Get or create circuit breaker.

    Args:
        name: Circuit breaker name
        failure_threshold: Number of failures before opening
        timeout: Seconds before attempting recovery
        expected_exception: Exception type that counts as failure

    Returns:
        Circuit breaker instance
    """
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(
            failure_threshold=failure_threshold,
            timeout=timeout,
            expected_exception=expected_exception,
            name=name,
        )

    return _circuit_breakers[name]


def get_all_circuit_breakers() -> dict[str, CircuitBreaker]:
    """Get all registered circuit breakers."""
    return _circuit_breakers.copy()

