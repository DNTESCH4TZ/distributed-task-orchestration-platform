"""
Celery Task Definitions.

Executes distributed tasks across workers.
"""

import logging
from typing import Any
from uuid import UUID

import httpx
from celery import Task

from src.core.constants import TaskTypeEnum
from src.infrastructure.messaging.celery.app import app

logger = logging.getLogger(__name__)


class CallbackTask(Task):
    """
    Base task with callbacks for task lifecycle events.

    Automatically updates task state in database.
    """

    def on_success(self, retval: Any, task_id: str, args: tuple, kwargs: dict) -> None:
        """Called when task succeeds."""
        logger.info(
            "Task succeeded",
            extra={
                "task_id": task_id,
                "result": retval,
            },
        )
        # TODO: Update task in database via orchestrator
        # await orchestrator.on_task_completed(UUID(task_id), retval)

    def on_failure(
        self,
        exc: Exception,
        task_id: str,
        args: tuple,
        kwargs: dict,
        einfo: Any,
    ) -> None:
        """Called when task fails."""
        logger.error(
            "Task failed",
            extra={
                "task_id": task_id,
                "error": str(exc),
            },
            exc_info=exc,
        )
        # TODO: Update task in database via orchestrator
        # await orchestrator.on_task_failed(UUID(task_id), str(exc))

    def on_retry(
        self,
        exc: Exception,
        task_id: str,
        args: tuple,
        kwargs: dict,
        einfo: Any,
    ) -> None:
        """Called when task is retried."""
        logger.warning(
            "Task retrying",
            extra={
                "task_id": task_id,
                "error": str(exc),
            },
        )


@app.task(
    base=CallbackTask,
    bind=True,
    name="execute_task",
    max_retries=3,
    default_retry_delay=60,
)
def execute_task(
    self: Task,
    task_id: str,
    task_type: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """
    Execute task based on type.

    Args:
        self: Celery task instance
        task_id: Task ID
        task_type: Type of task (http/python/sql/etc)
        payload: Task payload

    Returns:
        Task execution result
    """
    logger.info(
        "Executing task",
        extra={
            "task_id": task_id,
            "task_type": task_type,
        },
    )

    try:
        task_type_enum = TaskTypeEnum(task_type)

        if task_type_enum == TaskTypeEnum.HTTP:
            return execute_http_task.delay(task_id, payload).get()
        elif task_type_enum == TaskTypeEnum.PYTHON:
            return execute_python_task.delay(task_id, payload).get()
        elif task_type_enum == TaskTypeEnum.SQL:
            return execute_sql_task.delay(task_id, payload).get()
        elif task_type_enum == TaskTypeEnum.SHELL:
            return execute_shell_task.delay(task_id, payload).get()
        else:
            raise ValueError(f"Unsupported task type: {task_type}")

    except Exception as exc:
        logger.error(
            "Task execution failed",
            extra={
                "task_id": task_id,
                "error": str(exc),
            },
            exc_info=exc,
        )
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2**self.request.retries)


@app.task(name="execute_http_task", max_retries=3)
def execute_http_task(task_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """
    Execute HTTP task.

    Args:
        task_id: Task ID
        payload: HTTP request config (url, method, headers, body)

    Returns:
        HTTP response data
    """
    import asyncio

    async def _execute() -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=payload.get("method", "GET"),
                url=payload["url"],
                headers=payload.get("headers", {}),
                json=payload.get("body"),
            )
            response.raise_for_status()

            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.json() if response.headers.get("content-type") == "application/json" else response.text,
            }

    return asyncio.run(_execute())


@app.task(name="execute_python_task", max_retries=3)
def execute_python_task(task_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """
    Execute Python code task.

    Args:
        task_id: Task ID
        payload: Python code to execute

    Returns:
        Execution result

    Warning:
        This is a security risk! Only use with trusted code.
        In production, use sandboxing (e.g., RestrictedPython, PyPy sandbox)
    """
    logger.warning(
        "Executing Python code - security risk!",
        extra={"task_id": task_id},
    )

    # TODO: Implement sandboxing
    code = payload.get("code", "")
    context = payload.get("context", {})

    # Execute code in restricted environment
    result = {}
    exec(code, {"__builtins__": {}}, {"context": context, "result": result})

    return result


@app.task(name="execute_sql_task", max_retries=3)
def execute_sql_task(task_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """
    Execute SQL query task.

    Args:
        task_id: Task ID
        payload: SQL query and connection config

    Returns:
        Query results
    """
    # TODO: Implement SQL execution with proper connection pooling
    logger.info(
        "SQL task execution not yet implemented",
        extra={"task_id": task_id},
    )
    return {"rows": [], "count": 0}


@app.task(name="execute_shell_task", max_retries=3)
def execute_shell_task(task_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """
    Execute shell command task.

    Args:
        task_id: Task ID
        payload: Shell command config

    Returns:
        Command output

    Warning:
        This is a security risk! Use with caution.
    """
    import subprocess

    logger.warning(
        "Executing shell command - security risk!",
        extra={"task_id": task_id},
    )

    command = payload.get("command", "")
    timeout = payload.get("timeout", 300)

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True,
        )

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }

    except subprocess.TimeoutExpired as e:
        raise Exception(f"Command timed out after {timeout}s") from e
    except subprocess.CalledProcessError as e:
        raise Exception(f"Command failed with code {e.returncode}") from e


@app.task(name="execute_webhook_task", max_retries=3)
def execute_webhook_task(task_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """
    Execute webhook task (send HTTP POST notification).

    Args:
        task_id: Task ID
        payload: Webhook URL and data

    Returns:
        Webhook response
    """
    import asyncio

    async def _execute() -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url=payload["webhook_url"],
                json=payload.get("data", {}),
                headers=payload.get("headers", {}),
            )
            response.raise_for_status()

            return {
                "status_code": response.status_code,
                "delivered": True,
            }

    return asyncio.run(_execute())

