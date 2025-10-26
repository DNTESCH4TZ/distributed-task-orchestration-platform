"""
Prometheus Metrics Collectors.

Application-level metrics for monitoring.
"""

from prometheus_client import Counter, Gauge, Histogram, Summary

# ========================================
# HTTP Metrics
# ========================================

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests in progress",
    ["method", "endpoint"],
)

# ========================================
# Workflow Metrics
# ========================================

workflows_created_total = Counter(
    "workflows_created_total",
    "Total workflows created",
    ["execution_mode"],
)

workflows_started_total = Counter(
    "workflows_started_total",
    "Total workflows started",
)

workflows_completed_total = Counter(
    "workflows_completed_total",
    "Total workflows completed",
    ["status"],  # succeeded/failed/cancelled
)

workflow_duration_seconds = Histogram(
    "workflow_duration_seconds",
    "Workflow execution duration in seconds",
    buckets=[1, 5, 10, 30, 60, 300, 600, 1800, 3600],
)

workflows_active = Gauge(
    "workflows_active",
    "Number of currently active workflows",
)

# ========================================
# Task Metrics
# ========================================

tasks_created_total = Counter(
    "tasks_created_total",
    "Total tasks created",
    ["task_type"],
)

tasks_queued_total = Counter(
    "tasks_queued_total",
    "Total tasks queued for execution",
    ["task_type", "priority"],
)

tasks_started_total = Counter(
    "tasks_started_total",
    "Total tasks started",
    ["task_type"],
)

tasks_completed_total = Counter(
    "tasks_completed_total",
    "Total tasks completed",
    ["task_type", "status"],  # succeeded/failed/cancelled
)

tasks_retried_total = Counter(
    "tasks_retried_total",
    "Total task retry attempts",
    ["task_type"],
)

task_duration_seconds = Histogram(
    "task_duration_seconds",
    "Task execution duration in seconds",
    ["task_type"],
    buckets=[0.1, 0.5, 1, 5, 10, 30, 60, 300, 600],
)

tasks_in_progress = Gauge(
    "tasks_in_progress",
    "Number of tasks currently executing",
    ["task_type"],
)

# ========================================
# Database Metrics
# ========================================

db_connections_active = Gauge(
    "db_connections_active",
    "Number of active database connections",
)

db_connections_idle = Gauge(
    "db_connections_idle",
    "Number of idle database connections",
)

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation"],  # select/insert/update/delete
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

db_queries_total = Counter(
    "db_queries_total",
    "Total database queries",
    ["operation", "status"],  # success/error
)

# ========================================
# Redis Metrics
# ========================================

redis_operations_total = Counter(
    "redis_operations_total",
    "Total Redis operations",
    ["operation", "status"],  # get/set/delete, success/error
)

redis_cache_hits_total = Counter(
    "redis_cache_hits_total",
    "Total cache hits",
)

redis_cache_misses_total = Counter(
    "redis_cache_misses_total",
    "Total cache misses",
)

redis_operation_duration_seconds = Histogram(
    "redis_operation_duration_seconds",
    "Redis operation duration in seconds",
    ["operation"],
    buckets=[0.0001, 0.0005, 0.001, 0.005, 0.01, 0.025, 0.05, 0.1],
)

# ========================================
# Celery Metrics
# ========================================

celery_tasks_sent_total = Counter(
    "celery_tasks_sent_total",
    "Total Celery tasks sent",
    ["task_name"],
)

celery_tasks_received_total = Counter(
    "celery_tasks_received_total",
    "Total Celery tasks received by workers",
    ["task_name"],
)

celery_tasks_failed_total = Counter(
    "celery_tasks_failed_total",
    "Total Celery tasks failed",
    ["task_name", "exception_type"],
)

celery_task_runtime_seconds = Summary(
    "celery_task_runtime_seconds",
    "Celery task runtime in seconds",
    ["task_name"],
)

celery_workers_active = Gauge(
    "celery_workers_active",
    "Number of active Celery workers",
)

# ========================================
# Business Metrics
# ========================================

workflow_success_rate = Gauge(
    "workflow_success_rate",
    "Workflow success rate (0.0-1.0)",
)

task_success_rate = Gauge(
    "task_success_rate",
    "Task success rate (0.0-1.0)",
    ["task_type"],
)

average_workflow_duration = Gauge(
    "average_workflow_duration_seconds",
    "Average workflow duration in seconds",
)

# ========================================
# System Metrics (Optional)
# ========================================

system_cpu_usage = Gauge(
    "system_cpu_usage_percent",
    "System CPU usage percentage",
)

system_memory_usage = Gauge(
    "system_memory_usage_bytes",
    "System memory usage in bytes",
)

system_disk_usage = Gauge(
    "system_disk_usage_bytes",
    "System disk usage in bytes",
)

