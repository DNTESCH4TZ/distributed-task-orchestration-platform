"""
Pytest configuration and shared fixtures.

This file is automatically loaded by pytest and provides fixtures
that can be used across all test modules.
"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Will be implemented later
# from src.core.config import get_settings
# from src.infrastructure.database.models.base import Base
# from src.main import app


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Create event loop for async tests.

    Scope: session - one loop for all tests.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db_engine():
    """
    Create async database engine for testing.

    Uses NullPool to avoid connection pool issues in tests.
    """
    # TODO: Implement after config is created
    # settings = get_settings()
    # engine = create_async_engine(
    #     settings.TEST_DATABASE_URL,
    #     poolclass=NullPool,
    #     echo=False,
    # )
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    #
    # yield engine
    #
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.drop_all)
    # await engine.dispose()
    pass


@pytest.fixture
async def db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create database session for each test.

    Each test gets a fresh session that is rolled back after the test.
    """
    # TODO: Implement after database models are created
    # async_session = sessionmaker(
    #     test_db_engine,
    #     class_=AsyncSession,
    #     expire_on_commit=False,
    # )
    # async with async_session() as session:
    #     yield session
    #     await session.rollback()
    pass


@pytest.fixture
def client() -> TestClient:
    """
    Create FastAPI test client.

    Uses TestClient which handles lifespan events automatically.
    """
    # TODO: Implement after FastAPI app is created
    # return TestClient(app)
    pass


@pytest.fixture
def authenticated_client(client: TestClient) -> TestClient:
    """
    Create authenticated test client with valid JWT token.
    """
    # TODO: Implement after auth is created
    # token = create_test_token()
    # client.headers = {"Authorization": f"Bearer {token}"}
    # return client
    pass


@pytest.fixture
async def redis_client():
    """
    Create Redis client for testing.

    Uses separate Redis DB to avoid conflicts with development.
    """
    # TODO: Implement after Redis is configured
    # import redis.asyncio as redis
    # client = await redis.from_url("redis://localhost:6379/15")
    # yield client
    # await client.flushdb()  # Clean up after test
    # await client.close()
    pass


@pytest.fixture
def mock_celery_task():
    """
    Mock Celery task execution for testing.
    """
    # TODO: Implement after Celery is configured
    pass


# ========================================
# Markers
# ========================================

def pytest_configure(config):
    """
    Register custom pytest markers.
    """
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")
    config.addinivalue_line("markers", "unit: mark test as unit test")

