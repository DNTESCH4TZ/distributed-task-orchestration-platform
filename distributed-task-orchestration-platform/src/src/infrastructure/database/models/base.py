"""
Base model with common fields and utilities.

All database models inherit from this base.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID

from src.infrastructure.database.base import Base


class BaseModel(Base):
    """
    Abstract base model with common fields.

    All models inherit:
    - id (UUID primary key)
    - created_at (timestamp)
    - updated_at (timestamp, auto-updated)
    """

    __abstract__ = True

    id = Column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<{self.__class__.__name__}(id={self.id})>"

