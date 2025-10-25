#!/usr/bin/env python3
"""
Health Check Script.

Checks health of all application components.
"""

import asyncio
import sys

import httpx

from src.core.config import get_settings


async def check_api_health() -> bool:
    """Check API health."""
    settings = get_settings()
    url = f"http://localhost:8000/api/v1/health"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=5.0)
            response.raise_for_status()
            print("✅ API: healthy")
            return True
    except Exception as e:
        print(f"❌ API: unhealthy - {e}")
        return False


async def check_database_health() -> bool:
    """Check database health."""
    try:
        from src.infrastructure.database.base import engine
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        print("✅ Database: healthy")
        return True
    except Exception as e:
        print(f"❌ Database: unhealthy - {e}")
        return False


async def check_redis_health() -> bool:
    """Check Redis health."""
    try:
        from src.infrastructure.messaging.redis.client import get_redis

        redis = await get_redis()
        healthy = await redis.health_check()

        if healthy:
            print("✅ Redis: healthy")
            return True
        else:
            print("❌ Redis: unhealthy")
            return False
    except Exception as e:
        print(f"❌ Redis: unhealthy - {e}")
        return False


async def main() -> None:
    """Run all health checks."""
    print("🏥 Running health checks...\n")

    checks = [
        check_api_health(),
        check_database_health(),
        check_redis_health(),
    ]

    results = await asyncio.gather(*checks, return_exceptions=True)

    all_healthy = all(
        result is True for result in results if not isinstance(result, Exception)
    )

    print()
    if all_healthy:
        print("✅ All systems healthy!")
        sys.exit(0)
    else:
        print("❌ Some systems unhealthy")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

