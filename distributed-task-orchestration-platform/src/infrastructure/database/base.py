"""
Database Base Configuration.

Async SQLAlchemy setup with connection pooling for high performance.
"""

from typing import AsyncGenerator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool, QueuePool

from src.core.config import get_settings

settings = get_settings()

# ========================================
# Database Engine with Connection Pooling
# ========================================

# For production: use QueuePool for connection pooling
# For testing: use NullPool to avoid connection pool issues
PoolClass = NullPool if settings.is_testing else QueuePool

engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=settings.DATABASE_ECHO,
    future=True,
    poolclass=PoolClass,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    pool_pre_ping=True,  # Verify connections before using
)

# Read replica engine for CQRS (if configured)
read_engine = None
if settings.DATABASE_READ_URL:
    read_engine = create_async_engine(
        str(settings.DATABASE_READ_URL),
        echo=settings.DATABASE_ECHO,
        future=True,
        poolclass=PoolClass,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_timeout=settings.DATABASE_POOL_TIMEOUT,
        pool_recycle=settings.DATABASE_POOL_RECYCLE,
        pool_pre_ping=True,
    )

# ========================================
# Session Factory
# ========================================

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# Read-only session for CQRS
AsyncReadSessionLocal = None
if read_engine:
    AsyncReadSessionLocal = sessionmaker(
        read_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

# ========================================
# Metadata and Base
# ========================================

# Naming convention for constraints
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)
Base = declarative_base(metadata=metadata)


# ========================================
# Dependency Injection
# ========================================


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session.

    Yields:
        Async database session

    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_read_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async read-only database session (CQRS).

    Falls back to regular session if read replica not configured.

    Yields:
        Async read-only database session
    """
    session_factory = AsyncReadSessionLocal or AsyncSessionLocal
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


# ========================================
# Database Lifecycle
# ========================================


async def init_db() -> None:
    """Initialize database (create tables)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
    if read_engine:
        await read_engine.dispose()

