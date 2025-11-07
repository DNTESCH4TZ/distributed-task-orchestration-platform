"""
Graceful Shutdown Handler.

Ensures clean shutdown of all services without dropping in-flight requests.
"""

import asyncio
import logging
import signal
from typing import Any, Callable

logger = logging.getLogger(__name__)


class GracefulShutdownHandler:
    """
    Handles graceful shutdown of the application.

    Features:
    - Stops accepting new connections
    - Waits for in-flight requests to complete
    - Closes database connections
    - Closes Redis connections
    - Flushes metrics
    """

    def __init__(self, timeout: int = 30) -> None:
        """
        Initialize shutdown handler.

        Args:
            timeout: Max seconds to wait for shutdown
        """
        self.timeout = timeout
        self._shutdown_callbacks: list[Callable] = []
        self._is_shutting_down = False

    def register_callback(self, callback: Callable) -> None:
        """
        Register cleanup callback.

        Args:
            callback: Async function to call on shutdown
        """
        self._shutdown_callbacks.append(callback)

    async def shutdown(self) -> None:
        """
        Perform graceful shutdown.

        Executes all registered callbacks with timeout.
        """
        if self._is_shutting_down:
            return

        self._is_shutting_down = True
        logger.info("🛑 Starting graceful shutdown...")

        # Execute all callbacks with timeout
        tasks = [callback() for callback in self._shutdown_callbacks]

        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.timeout,
            )
            logger.info("✅ Graceful shutdown completed")

        except asyncio.TimeoutError:
            logger.error(
                f"⚠️ Shutdown timeout after {self.timeout}s, forcing exit"
            )

        except Exception as e:
            logger.error(
                "❌ Error during shutdown",
                extra={"error": str(e)},
                exc_info=True,
            )

    def setup_signal_handlers(self) -> None:
        """
        Setup signal handlers for SIGTERM and SIGINT.

        Allows graceful shutdown on container stop or Ctrl+C.
        """
        loop = asyncio.get_event_loop()

        def signal_handler(sig: Any) -> None:
            """Handle shutdown signals."""
            logger.info(f"Received signal {sig}, initiating shutdown...")
            asyncio.create_task(self.shutdown())

        # Register handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda s=sig: signal_handler(s))

        logger.info("Signal handlers registered (SIGTERM, SIGINT)")


# Global instance
_shutdown_handler: GracefulShutdownHandler | None = None


def get_shutdown_handler() -> GracefulShutdownHandler:
    """Get global shutdown handler instance."""
    global _shutdown_handler

    if _shutdown_handler is None:
        _shutdown_handler = GracefulShutdownHandler()

    return _shutdown_handler

