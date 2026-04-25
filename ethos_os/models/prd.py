"""PRD model - Product Requirements Document."""

import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import Mapped, mapped_column

from ethos_os.models.base import Base, UUIDMixin, TimestampMixin


class PRDStatus(enum.Enum):
    """PRD status workflow."""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class PRD(Base, UUIDMixin, TimestampMixin):
    """PRD - Product Requirements Document.
    
    The primary governance artifact. Board reviews and approves scope.
    - One PRD per Project
    - Status workflow: draft → pending_review → approved/rejected
    """
    
    __tablename__ = "prds"

    # FK to Project
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One PRD per project
    )
    
    # Intent - one-line objective
    intent: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Success metric - measurable criteria
    success_metric: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Scope - what's included
    scope: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Boundaries - explicit exclusions
    boundaries: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Timeline - JSON {start, end, milestones: [{name, date}]}
    timeline: Mapped[dict | None] = mapped_column(SQLiteJSON, nullable=True)
    
    # Budget - in cents
    budget: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=PRDStatus.DRAFT.value,
    )
    
    # Qdrant vector storage for content embeddings
    qdrant_collection_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    qdrant_point_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    
    # Created by
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    
    # Reviewed by
    reviewed_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self) -> str:
        return f"<PRD(id={self.id}, project_id={self.project_id}, status={self.status})>"