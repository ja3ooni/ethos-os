"""Project model - deliverable with board-approved PRD."""

import enum

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import Mapped, mapped_column

from ethos_os.models.base import Base, UUIDMixin, TimestampMixin, OwnerMixin, PathMixin


class ProjectStatus(enum.Enum):
    """Project PRD status workflow."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    ARCHIVED = "archived"


class Project(Base, UUIDMixin, TimestampMixin, OwnerMixin, PathMixin):
    """Project - a deliverable with board-approved PRD.
    
    Projects contain sprints and must have an approved PRD before spawning sprints.
    - path_depth: 3
    - Parent: Program
    - Has: prd_status enum (draft → pending_approval → approved → archived)
    """
    
    __tablename__ = "projects"

    # Name
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # FK to Program
    program_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # PRD Status
    prd_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ProjectStatus.DRAFT.value,
    )
    
    # Intent - one-line objective
    intent: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Success metric - measurable criteria
    success_metric: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Scope - what's included
    scope: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Boundaries - explicit exclusions
    boundaries: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Timeline - JSON {start, end, milestones}
    timeline: Mapped[dict | None] = mapped_column(SQLiteJSON, nullable=True)
    
    # Budget - in cents
    budget: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Qdrant vector storage (for PRD content embeddings)
    qdrant_collection_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    qdrant_point_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    
    # Override path depth
    path_depth: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    
    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name={self.name}, status={self.prd_status})>"