"""Base model and mixins for EthosOS domain entities.

Provides:
- UUIDMixin: UUID primary key with auto-generation
- TimestampMixin: created_at, updated_at with server-side defaults
- OwnerMixin: owner_id for tracking entity ownership
- PathMixin: materialized path for O(1) lineage queries
"""

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, Integer, String
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from ethos_os.db import Base


class UUIDMixin:
    """Mixin providing UUID primary key."""

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )


class TimestampMixin:
    """Mixin providing created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class OwnerMixin:
    """Mixin providing owner_id for tracking ownership."""

    owner_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
    )


class PathMixin:
    """Mixin providing materialized path for lineage queries.
    
    Format: /uuid/uuid/uuid/...
    - parent_id: FK to parent entity (null for root)
    - path: materialized path string
    - path_depth: level in hierarchy (1=portfolio, 2=program, etc.)
    """

    parent_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        doc="FK to parent entity (null for root entities)"
    )

    path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Materialized path: /uuid/uuid/uuid/..."
    )

    path_depth: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Level in hierarchy: 1=portfolio, 2=program, 3=project, 4=sprint, 5=task"
    )


def compute_path(parent_path: str | None, entity_id: str) -> str:
    """Compute materialized path for a new entity.
    
    Args:
        parent_path: Path of parent entity (None for root)
        entity_id: UUID of this entity
    
    Returns:
        Materialized path string, e.g., "/uuid1/uuid2/"
    """
    if parent_path is None:
        return f"/{entity_id}/"
    return f"{parent_path}{entity_id}/"


def get_lineage_from_path(path: str) -> list[str]:
    """Extract lineage UUIDs from materialized path.
    
    Args:
        path: Materialized path string like "/uuid1/uuid2/uuid3/"
    
    Returns:
        List of UUIDs in order: [portfolio_id, program_id, ...]
    """
    if not path:
        return []
    # Remove leading/trailing slashes, split by /
    segments = path.strip("/").split("/")
    return [s for s in segments if s]  # Filter empty strings