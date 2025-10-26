"""
FastAPI Application Entry Point.

High-performance async application optimized for 1M+ RPS.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvloop
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse

from src.api.middleware.correlation_id import CorrelationIdMiddleware
from src.api.middleware.error_handler import ErrorHandlerMiddleware
from src.api.middleware.metrics import MetricsMiddleware
from src.api.v1.endpoints import health, workflows
from src.core.config import get_settings
from src.infrastructure.database.base import close_db, init_db

# Use uvloop for faster async performance (2-4x improvement)
uvloop.install()

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan events.

    Handles startup and shutdown operations.
    """
    # Startup
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📊 Environment: {settings.ENVIRONMENT}")

    # Initialize database
    if not settings.is_testing:
        await init_db()
        print("✅ Database initialized")

    # TODO: Initialize Redis connection pool
    # TODO: Initialize metrics collectors

    yield

    # Shutdown
    print("🛑 Shutting down gracefully...")
    await close_db()
    print("✅ Database connections closed")
    # TODO: Close Redis connections
    # TODO: Flush metrics


def create_app() -> FastAPI:
    """
    Factory function to create FastAPI application.

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Production-grade distributed task orchestration platform",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        default_response_class=ORJSONResponse,  # Faster JSON serialization
        lifespan=lifespan,
    )

    # ========================================
    # Middleware (order matters!)
    # ========================================

    # 1. Metrics middleware (first to measure everything)
    app.add_middleware(MetricsMiddleware)

    # 2. Correlation ID for distributed tracing
    app.add_middleware(CorrelationIdMiddleware)

    # 3. Error handling
    app.add_middleware(ErrorHandlerMiddleware)

    # 4. CORS
    if settings.CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
            allow_methods=settings.CORS_ALLOW_METHODS,
            allow_headers=settings.CORS_ALLOW_HEADERS,
        )

    # 5. GZip compression for responses > 1KB
    app.add_middleware(GZipMiddleware, minimum_size=1024)

    # ========================================
    # Routes
    # ========================================

    # Health check endpoint
    app.include_router(
        health.router,
        prefix=settings.API_V1_PREFIX,
        tags=["health"],
    )

    # Workflow endpoints
    app.include_router(
        workflows.router,
        prefix=settings.API_V1_PREFIX,
        tags=["workflows"],
    )

    # TODO: Add task endpoints
    # TODO: Add analytics endpoints
    # TODO: Add admin endpoints
    # TODO: Add WebSocket endpoints

    return app


# Create application instance
app = create_app()


# ========================================
# Root endpoint
# ========================================


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    """Root endpoint with API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs" if not settings.is_production else "disabled",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        loop="uvloop",  # Use uvloop
        http="httptools",  # Use httptools for faster HTTP parsing
        workers=1 if settings.is_development else settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=settings.is_development,
    )
