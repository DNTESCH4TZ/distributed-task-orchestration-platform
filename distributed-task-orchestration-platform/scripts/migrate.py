#!/usr/bin/env python3
"""
Database migration script.

Runs Alembic migrations programmatically.
"""

import asyncio
import sys

from alembic import command
from alembic.config import Config

from src.core.config import get_settings


def run_migrations(command_name: str = "upgrade", revision: str = "head") -> None:
    """
    Run database migrations.

    Args:
        command_name: Alembic command (upgrade, downgrade, etc.)
        revision: Target revision (head, +1, -1, etc.)
    """
    settings = get_settings()

    print(f"🔄 Running migrations: {command_name} {revision}")
    print(f"📊 Environment: {settings.ENVIRONMENT}")
    print(f"🗄️  Database: {settings.DATABASE_URL}")

    # Load Alembic config
    alembic_cfg = Config("alembic.ini")

    # Override database URL from settings
    alembic_cfg.set_main_option("sqlalchemy.url", str(settings.DATABASE_URL))

    # Run command
    try:
        if command_name == "upgrade":
            command.upgrade(alembic_cfg, revision)
        elif command_name == "downgrade":
            command.downgrade(alembic_cfg, revision)
        elif command_name == "current":
            command.current(alembic_cfg)
        elif command_name == "history":
            command.history(alembic_cfg)
        else:
            print(f"❌ Unknown command: {command_name}")
            sys.exit(1)

        print("✅ Migrations completed successfully")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        rev = sys.argv[2] if len(sys.argv) > 2 else "head"
        run_migrations(cmd, rev)
    else:
        run_migrations()

