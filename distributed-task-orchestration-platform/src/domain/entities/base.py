"""
Base Entity class for Domain-Driven Design.

All domain entities inherit from this base class.
"""

from abc import ABC
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4


class BaseEntity(ABC):
    """
    Base class for all domain entities.

    Entities have identity (ID) and lifecycle.
    Two entities are equal if they have the same ID.
    """

    def __init__(self, id: UUID | None = None) -> None:
        """
        Initialize entity with optional ID.

        Args:
            id: Entity identifier. If None, generates new UUID.
        """
        self._id = id or uuid4()
        self._created_at = datetime.utcnow()
        self._updated_at = datetime.utcnow()

    @property
    def id(self) -> UUID:
        """Get entity ID."""
        return self._id

    @property
    def created_at(self) -> datetime:
        """Get creation timestamp."""
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        """Get last update timestamp."""
        return self._updated_at

    def _mark_updated(self) -> None:
        """Mark entity as updated (internal use)."""
        self._updated_at = datetime.utcnow()

    def __eq__(self, other: Any) -> bool:
        """Two entities are equal if they have the same ID."""
        if not isinstance(other, BaseEntity):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on ID for use in sets/dicts."""
        return hash(self.id)

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(id={self.id})"

