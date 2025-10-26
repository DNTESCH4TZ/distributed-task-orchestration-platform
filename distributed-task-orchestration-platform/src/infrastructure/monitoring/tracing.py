"""
Distributed Tracing with OpenTelemetry.

Sends traces to Jaeger for distributed request tracing.
"""

import logging

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBasedTraceIdRatio

from src.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def setup_tracing(app: any) -> None:
    """
    Setup distributed tracing with OpenTelemetry + Jaeger.

    Args:
        app: FastAPI application instance
    """
    if not settings.JAEGER_ENABLED:
        logger.info("Tracing disabled")
        return

    # Create resource with service metadata
    resource = Resource.create({
        "service.name": settings.APP_NAME,
        "service.version": settings.APP_VERSION,
        "deployment.environment": settings.ENVIRONMENT,
    })

    # Configure tracer provider with sampling
    sampler = ParentBasedTraceIdRatio(settings.JAEGER_SAMPLER_PARAM)
    
    provider = TracerProvider(
        resource=resource,
        sampler=sampler,
    )

    # Configure Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name=settings.JAEGER_AGENT_HOST,
        agent_port=settings.JAEGER_AGENT_PORT,
    )

    # Use batch processor for performance
    span_processor = BatchSpanProcessor(jaeger_exporter)
    provider.add_span_processor(span_processor)

    # Set as global tracer provider
    trace.set_tracer_provider(provider)

    # Instrument FastAPI automatically
    FastAPIInstrumentor.instrument_app(app)

    logger.info(
        "Tracing enabled",
        extra={
            "jaeger_host": settings.JAEGER_AGENT_HOST,
            "jaeger_port": settings.JAEGER_AGENT_PORT,
            "sampling_rate": settings.JAEGER_SAMPLER_PARAM,
        },
    )


def get_tracer(name: str) -> trace.Tracer:
    """
    Get tracer for creating custom spans.

    Usage:
        tracer = get_tracer(__name__)
        with tracer.start_as_current_span("operation_name"):
            # Your code here
            ...

    Args:
        name: Tracer name (usually __name__)

    Returns:
        Tracer instance
    """
    return trace.get_tracer(name)


def add_span_attributes(**attributes: any) -> None:
    """
    Add attributes to current span.

    Usage:
        add_span_attributes(
            workflow_id=str(workflow.id),
            task_count=len(workflow.tasks),
        )

    Args:
        **attributes: Key-value pairs to add to span
    """
    span = trace.get_current_span()
    if span.is_recording():
        for key, value in attributes.items():
            span.set_attribute(key, value)


def add_span_event(name: str, **attributes: any) -> None:
    """
    Add event to current span.

    Usage:
        add_span_event(
            "task_queued",
            task_id=str(task.id),
            task_type=task.config.task_type,
        )

    Args:
        name: Event name
        **attributes: Event attributes
    """
    span = trace.get_current_span()
    if span.is_recording():
        span.add_event(name, attributes=attributes)

