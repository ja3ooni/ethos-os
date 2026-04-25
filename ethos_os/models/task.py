"""Task model - atomic unit of work derived from PRD."""

import enum

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ethos_os.models.base import Base, UUIDMixin, TimestampMixin, OwnerMixin, PathMixin


class TaskStatus(enum.Enum):
    """Task status."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"


class Task(Base, UUIDMixin, TimestampMixin, OwnerMixin, PathMixin):
    """Task - atomic unit of work derived from board-approved PRD.
    
    - path_depth: 5
    - Parent: Sprint
    - Validation: prd_scope_item_id is required (no orphan tasks)
    """
    
    __tablename__ = "tasks"

    # Name
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # FK to Sprint
    sprint_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sprints.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # PRD scope item reference - REQUIRED (D-44)
    prd_scope_item_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        doc="Reference to PRD scope section - must not be null"
    )
    
    # Effort estimate in hours
    effort_estimate_hours: Mapped[int | None] = mapped_column(Numeric(10, 2), nullable=True)
    
    # Assignee (agent or human)
    assignee_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=TaskStatus.TODO.value,
    )
    
    # Description
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Override path depth
    path_depth: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    
    def __repr__(self) -> str:
        return f"<Task(id={self.id}, name={self.name}, status={self.status})>"