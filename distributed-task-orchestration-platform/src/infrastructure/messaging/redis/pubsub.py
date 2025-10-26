"""
Redis Pub/Sub for Event-Driven Architecture.

Publishes and subscribes to domain events.
"""

import asyncio
import logging
from typing import Any, Callable

import orjson
import redis.asyncio as redis

from src.core.config import get_settings
from src.core.events import DomainEvent

logger = logging.getLogger(__name__)
settings = get_settings()


class EventPublisher:
    """
    Publishes domain events to Redis Pub/Sub.

    Events are serialized with orjson for performance.
    """

    def __init__(self) -> None:
        """Initialize event publisher."""
        self._client: redis.Redis | None = None

    async def connect(self) -> None:
        """Connect to Redis."""
        self._client = redis.from_url(str(settings.REDIS_URL))
        await self._client.ping()
        logger.info("Event publisher connected to Redis")

    async def close(self) -> None:
        """Close connection."""
        if self._client:
            await self._client.close()

    async def publish(self, channel: str, event: DomainEvent) -> int:
        """
        Publish event to channel.

        Args:
            channel: Channel name
            event: Domain event to publish

        Returns:
            Number of subscribers that received the message
        """
        if self._client is None:
            raise RuntimeError("Publisher not connected")

        # Serialize event
        event_data = {
            "event_id": str(event.event_id),
            "timestamp": event.timestamp.isoformat(),
            "aggregate_id": str(event.aggregate_id),
            "aggregate_type": event.aggregate_type,
            "event_type": event.event_type,
            "metadata": event.metadata,
        }

        # Add event-specific data
        for key, value in event.__dict__.items():
            if key not in event_data:
                event_data[key] = str(value) if hasattr(value, "__str__") else value

        serialized = orjson.dumps(event_data)

        # Publish to channel
        subscribers = await self._client.publish(channel, serialized)

        logger.debug(
            "Event published",
            extra={
                "channel": channel,
                "event_type": event.event_type,
                "subscribers": subscribers,
            },
        )

        return subscribers


class EventSubscriber:
    """
    Subscribes to domain events from Redis Pub/Sub.

    Runs event handlers in background.
    """

    def __init__(self) -> None:
        """Initialize event subscriber."""
        self._client: redis.Redis | None = None
        self._pubsub: redis.client.PubSub | None = None
        self._handlers: dict[str, list[Callable]] = {}
        self._task: asyncio.Task | None = None

    async def connect(self) -> None:
        """Connect to Redis and start listening."""
        self._client = redis.from_url(str(settings.REDIS_URL))
        self._pubsub = self._client.pubsub()
        await self._client.ping()
        logger.info("Event subscriber connected to Redis")

    async def subscribe(
        self,
        channel: str,
        handler: Callable[[dict[str, Any]], None],
    ) -> None:
        """
        Subscribe to channel and register handler.

        Args:
            channel: Channel name to subscribe
            handler: Async function to handle events
        """
        if self._pubsub is None:
            raise RuntimeError("Subscriber not connected")

        # Register handler
        if channel not in self._handlers:
            self._handlers[channel] = []
        self._handlers[channel].append(handler)

        # Subscribe to channel
        await self._pubsub.subscribe(channel)
        logger.info(f"Subscribed to channel: {channel}")

    async def start(self) -> None:
        """Start listening for events (blocking)."""
        if self._pubsub is None:
            raise RuntimeError("Subscriber not connected")

        logger.info("Event subscriber started")

        try:
            async for message in self._pubsub.listen():
                if message["type"] == "message":
                    channel = message["channel"].decode("utf-8")
                    data = orjson.loads(message["data"])

                    # Call all handlers for this channel
                    handlers = self._handlers.get(channel, [])
                    for handler in handlers:
                        try:
                            if asyncio.iscoroutinefunction(handler):
                                await handler(data)
                            else:
                                handler(data)
                        except Exception as e:
                            logger.error(
                                "Error in event handler",
                                extra={
                                    "channel": channel,
                                    "error": str(e),
                                },
                                exc_info=True,
                            )

        except Exception as e:
            logger.error(
                "Event subscriber error",
                extra={"error": str(e)},
                exc_info=True,
            )

    async def close(self) -> None:
        """Close connection."""
        if self._pubsub:
            await self._pubsub.close()
        if self._client:
            await self._client.close()
        logger.info("Event subscriber closed")


# Global instances
_event_publisher: EventPublisher | None = None
_event_subscriber: EventSubscriber | None = None


async def get_event_publisher() -> EventPublisher:
    """Get event publisher instance."""
    global _event_publisher

    if _event_publisher is None:
        _event_publisher = EventPublisher()
        await _event_publisher.connect()

    return _event_publisher


async def get_event_subscriber() -> EventSubscriber:
    """Get event subscriber instance."""
    global _event_subscriber

    if _event_subscriber is None:
        _event_subscriber = EventSubscriber()
        await _event_subscriber.connect()

    return _event_subscriber


async def close_pubsub() -> None:
    """Close pub/sub connections."""
    global _event_publisher, _event_subscriber

    if _event_publisher:
        await _event_publisher.close()
        _event_publisher = None

    if _event_subscriber:
        await _event_subscriber.close()
        _event_subscriber = None

