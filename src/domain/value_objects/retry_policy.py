"""
Retry Policy Value Object.

Immutable value object defining retry behavior for failed tasks.
"""

from dataclasses import dataclass
from typing import Literal

from src.core.constants import (
    DEFAULT_RETRY_DELAY,
    EXPONENTIAL_BACKOFF_BASE,
    MAX_EXPONENTIAL_BACKOFF,
    MAX_RETRIES,
    RetryStrategyEnum,
)


@dataclass(frozen=True)
class RetryPolicy:
    """
    Retry policy for task execution.

    Value Object (immutable) - represents retry configuration.
    """

    max_retries: int = MAX_RETRIES
    strategy: RetryStrategyEnum = RetryStrategyEnum.EXPONENTIAL
    initial_delay: int = DEFAULT_RETRY_DELAY  # seconds
    max_delay: int = MAX_EXPONENTIAL_BACKOFF  # seconds
    backoff_base: int = EXPONENTIAL_BACKOFF_BASE  # for exponential strategy

    def __post_init__(self) -> None:
        """Validate retry policy parameters."""
        if self.max_retries < 0:
            raise ValueError("max_retries must be >= 0")

        if self.initial_delay < 0:
            raise ValueError("initial_delay must be >= 0")

        if self.max_delay < self.initial_delay:
            raise ValueError("max_delay must be >= initial_delay")

        if self.backoff_base < 1:
            raise ValueError("backoff_base must be >= 1")

    def calculate_delay(self, attempt: int) -> int:
        """
        Calculate delay before next retry based on strategy.

        Args:
            attempt: Current retry attempt (0-indexed)

        Returns:
            Delay in seconds before next retry
        """
        if attempt >= self.max_retries:
            return 0

        match self.strategy:
            case RetryStrategyEnum.NONE:
                return 0

            case RetryStrategyEnum.FIXED:
                return self.initial_delay

            case RetryStrategyEnum.LINEAR:
                delay = self.initial_delay * (attempt + 1)
                return min(delay, self.max_delay)

            case RetryStrategyEnum.EXPONENTIAL:
                # exponential: initial_delay * (backoff_base ^ attempt)
                delay = self.initial_delay * (self.backoff_base**attempt)
                return min(delay, self.max_delay)

            case _:
                return self.initial_delay

    def should_retry(self, attempt: int) -> bool:
        """
        Check if task should be retried.

        Args:
            attempt: Current retry attempt (0-indexed)

        Returns:
            True if should retry, False otherwise
        """
        return attempt < self.max_retries

    @classmethod
    def no_retry(cls) -> "RetryPolicy":
        """Create policy with no retries."""
        return cls(max_retries=0, strategy=RetryStrategyEnum.NONE)

    @classmethod
    def default(cls) -> "RetryPolicy":
        """Create default retry policy (exponential backoff)."""
        return cls()

    @classmethod
    def fixed_delay(cls, max_retries: int, delay: int) -> "RetryPolicy":
        """
        Create policy with fixed delay between retries.

        Args:
            max_retries: Maximum number of retries
            delay: Fixed delay in seconds
        """
        return cls(
            max_retries=max_retries,
            strategy=RetryStrategyEnum.FIXED,
            initial_delay=delay,
        )

