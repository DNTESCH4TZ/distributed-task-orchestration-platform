"""
Celery Application Configuration.

Configured for high performance with msgpack serialization.
"""

from celery import Celery

from src.core.config import get_settings

settings = get_settings()

# Create Celery app
app = Celery(
    "task-orchestrator",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Configure Celery
app.conf.update(
    # Serialization (msgpack is faster and more compact than JSON)
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    accept_content=settings.CELERY_ACCEPT_CONTENT,
    # Timezone
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=settings.CELERY_ENABLE_UTC,
    # Performance tuning for high throughput
    worker_prefetch_multiplier=settings.CELERY_WORKER_PREFETCH_MULTIPLIER,
    worker_max_tasks_per_child=settings.CELERY_WORKER_MAX_TASKS_PER_CHILD,
    task_acks_late=settings.CELERY_TASK_ACKS_LATE,
    task_reject_on_worker_lost=settings.CELERY_TASK_REJECT_ON_WORKER_LOST,
    # Result expiration
    result_expires=3600,  # 1 hour
    # Task routing
    task_routes={
        "src.infrastructure.messaging.celery.tasks.execute_task": {
            "queue": "tasks",
        },
        "src.infrastructure.messaging.celery.tasks.execute_http_task": {
            "queue": "http",
        },
        "src.infrastructure.messaging.celery.tasks.execute_python_task": {
            "queue": "python",
        },
    },
    # Task priority
    task_queue_max_priority=10,
    task_default_priority=5,
    # Monitoring
    task_send_sent_event=True,
    worker_send_task_events=True,
)

# Auto-discover tasks
app.autodiscover_tasks(["src.infrastructure.messaging.celery"])

