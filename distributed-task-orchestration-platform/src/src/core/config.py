"""
Application configuration using Pydantic Settings.

Reads from environment variables and .env file.
Optimized for high-performance (1M RPS target).
"""

from functools import lru_cache
from typing import List

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with validation.

    All settings can be overridden via environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ========================================
    # Application
    # ========================================
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=False)
    APP_NAME: str = Field(default="Task Orchestrator")
    APP_VERSION: str = Field(default="0.1.0")
    API_V1_PREFIX: str = Field(default="/api/v1")

    # Performance tuning for 1M RPS
    WORKERS: int = Field(default=4, description="Number of uvicorn workers")
    WORKER_CONNECTIONS: int = Field(
        default=1000, description="Max concurrent connections per worker"
    )
    BACKLOG: int = Field(default=2048, description="Socket listen backlog")

    # ========================================
    # Database - PostgreSQL
    # ========================================
    DATABASE_URL: PostgresDsn = Field(
        default="postgresql+asyncpg://orchestrator:orchestrator@localhost:5432/task_orchestrator"
    )
    DATABASE_POOL_SIZE: int = Field(default=20)
    DATABASE_MAX_OVERFLOW: int = Field(default=10)
    DATABASE_POOL_TIMEOUT: int = Field(default=30)
    DATABASE_POOL_RECYCLE: int = Field(default=3600)
    DATABASE_ECHO: bool = Field(default=False)

    # Read replica for CQRS (optional)
    DATABASE_READ_URL: PostgresDsn | None = None

    # ========================================
    # Redis - Cache & Pub/Sub
    # ========================================
    REDIS_URL: RedisDsn = Field(default="redis://localhost:6379/0")
    REDIS_MAX_CONNECTIONS: int = Field(default=50)
    REDIS_SOCKET_KEEPALIVE: bool = Field(default=True)
    REDIS_SOCKET_CONNECT_TIMEOUT: int = Field(default=5)
    REDIS_HEALTH_CHECK_INTERVAL: int = Field(default=30)

    # Redis for Celery
    REDIS_CELERY_URL: RedisDsn = Field(default="redis://localhost:6379/1")

    # Redis for rate limiting
    REDIS_RATE_LIMIT_URL: RedisDsn = Field(default="redis://localhost:6379/2")

    # ========================================
    # Message Queue - RabbitMQ & Celery
    # ========================================
    RABBITMQ_URL: str = Field(default="amqp://guest:guest@localhost:5672//")
    CELERY_BROKER_URL: str = Field(default="amqp://guest:guest@localhost:5672//")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/1")
    CELERY_TASK_SERIALIZER: str = Field(default="msgpack")
    CELERY_RESULT_SERIALIZER: str = Field(default="msgpack")
    CELERY_ACCEPT_CONTENT: List[str] = Field(default=["msgpack", "json"])
    CELERY_TIMEZONE: str = Field(default="UTC")
    CELERY_ENABLE_UTC: bool = Field(default=True)

    # Celery performance tuning
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = Field(default=4)
    CELERY_WORKER_MAX_TASKS_PER_CHILD: int = Field(default=1000)
    CELERY_TASK_ACKS_LATE: bool = Field(default=True)
    CELERY_TASK_REJECT_ON_WORKER_LOST: bool = Field(default=True)

    # ========================================
    # ClickHouse - Analytics
    # ========================================
    CLICKHOUSE_HOST: str = Field(default="localhost")
    CLICKHOUSE_PORT: int = Field(default=9000)
    CLICKHOUSE_USER: str = Field(default="default")
    CLICKHOUSE_PASSWORD: str = Field(default="")
    CLICKHOUSE_DATABASE: str = Field(default="task_orchestrator_analytics")

    # ========================================
    # Security
    # ========================================
    SECRET_KEY: str = Field(
        default="your-super-secret-key-change-in-production-min-32-chars"
    )
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"]
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True)
    CORS_ALLOW_METHODS: List[str] = Field(default=["*"])
    CORS_ALLOW_HEADERS: List[str] = Field(default=["*"])

    # ========================================
    # Observability
    # ========================================
    PROMETHEUS_ENABLED: bool = Field(default=True)
    PROMETHEUS_PORT: int = Field(default=9090)

    # Tracing - Jaeger
    JAEGER_ENABLED: bool = Field(default=True)
    JAEGER_AGENT_HOST: str = Field(default="localhost")
    JAEGER_AGENT_PORT: int = Field(default=6831)
    JAEGER_SAMPLER_TYPE: str = Field(default="probabilistic")
    JAEGER_SAMPLER_PARAM: float = Field(default=0.1)

    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(default="json")
    LOG_FILE: str = Field(default="logs/app.log")

    # ========================================
    # Rate Limiting
    # ========================================
    RATE_LIMIT_ENABLED: bool = Field(default=True)
    RATE_LIMIT_PER_MINUTE: int = Field(default=1000)
    RATE_LIMIT_PER_HOUR: int = Field(default=10000)

    # ========================================
    # Circuit Breaker
    # ========================================
    CIRCUIT_BREAKER_FAIL_THRESHOLD: int = Field(default=5)
    CIRCUIT_BREAKER_TIMEOUT: int = Field(default=60)

    # ========================================
    # Retry Policy
    # ========================================
    DEFAULT_MAX_RETRIES: int = Field(default=3)
    DEFAULT_RETRY_BACKOFF_BASE: int = Field(default=2)
    DEFAULT_RETRY_BACKOFF_MAX: int = Field(default=60)

    # ========================================
    # Workflow Settings
    # ========================================
    MAX_WORKFLOW_DEPTH: int = Field(default=10)
    MAX_PARALLEL_TASKS: int = Field(default=100)
    TASK_TIMEOUT_DEFAULT: int = Field(default=300)
    WORKFLOW_RETENTION_DAYS: int = Field(default=30)

    # ========================================
    # Performance Monitoring
    # ========================================
    SLOW_QUERY_THRESHOLD_MS: int = Field(default=100)
    REQUEST_TIMEOUT: int = Field(default=30)

    # ========================================
    # Testing
    # ========================================
    TESTING: bool = Field(default=False)
    TEST_DATABASE_URL: PostgresDsn | None = None

    # ========================================
    # Validators
    # ========================================

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v.upper()

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment."""
        allowed = {"development", "staging", "production", "test"}
        if v.lower() not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v.lower()

    # ========================================
    # Helper Properties
    # ========================================

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENVIRONMENT == "development"

    @property
    def is_testing(self) -> bool:
        """Check if running tests."""
        return self.TESTING or self.ENVIRONMENT == "test"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Using lru_cache ensures settings are loaded only once.
    """
    return Settings()

