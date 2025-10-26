"""
Celery Worker Configuration.

Optimized worker settings for production.
"""

from celery import bootsteps
from celery.signals import worker_ready, worker_shutdown

from src.infrastructure.messaging.celery.app import app


class DatabaseConnectionStep(bootsteps.StartStopStep):
    """
    Worker step to initialize database connections.

    Runs when worker starts.
    """

    def start(self, worker: any) -> None:
        """Initialize database connection pool."""
        print("📊 Initializing database connection pool...")
        # TODO: Initialize database connection pool
        # asyncio.run(init_db())

    def stop(self, worker: any) -> None:
        """Close database connections."""
        print("📊 Closing database connections...")
        # TODO: Close database connections
        # asyncio.run(close_db())


class RedisConnectionStep(bootsteps.StartStopStep):
    """
    Worker step to initialize Redis connections.

    Runs when worker starts.
    """

    def start(self, worker: any) -> None:
        """Initialize Redis connection pool."""
        print("🔴 Initializing Redis connection pool...")
        # TODO: Initialize Redis
        # asyncio.run(get_redis())

    def stop(self, worker: any) -> None:
        """Close Redis connections."""
        print("🔴 Closing Redis connections...")
        # TODO: Close Redis
        # asyncio.run(close_redis())


# Register steps
app.steps["worker"].add(DatabaseConnectionStep)
app.steps["worker"].add(RedisConnectionStep)


@worker_ready.connect
def on_worker_ready(**kwargs: any) -> None:
    """Called when worker is ready to receive tasks."""
    print("✅ Celery worker ready!")


@worker_shutdown.connect
def on_worker_shutdown(**kwargs: any) -> None:
    """Called when worker is shutting down."""
    print("👋 Celery worker shutting down...")


# Worker configuration for CLI
def get_worker_config() -> dict:
    """
    Get optimized worker configuration.

    Returns:
        Worker config dict
    """
    return {
        "concurrency": 4,  # Number of worker processes
        "prefetch_multiplier": 4,  # Tasks to prefetch per worker
        "max_tasks_per_child": 1000,  # Restart worker after N tasks (prevent memory leaks)
        "task_acks_late": True,  # Acknowledge task after completion
        "worker_lost_wait": 10,  # Seconds to wait for lost worker
        "task_reject_on_worker_lost": True,  # Reject task if worker dies
        # Queues to consume
        "queues": ["tasks", "http", "python", "default"],
        # Log level
        "loglevel": "INFO",
    }


if __name__ == "__main__":
    # Start worker with optimized config
    config = get_worker_config()
    app.worker_main(argv=[
        "worker",
        f"--concurrency={config['concurrency']}",
        f"--prefetch-multiplier={config['prefetch_multiplier']}",
        f"--max-tasks-per-child={config['max_tasks_per_child']}",
        f"--loglevel={config['loglevel']}",
        f"--queues={','.join(config['queues'])}",
    ])

