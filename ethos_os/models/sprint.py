"""Sprint model - time-boxed iteration."""

import enum
from datetime import date

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ethos_os.models.base import Base, UUIDMixin, TimestampMixin, OwnerMixin, PathMixin


class SprintStatus(enum.Enum):
    """Sprint status."""
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Sprint(Base, UUIDMixin, TimestampMixin, OwnerMixin, PathMixin):
    """Sprint - a time-boxed iteration within a project.
    
    Sprints have start, end dates and capacity.
    - path_depth: 4
    - Parent: Project
    - Validation: project.prd_status must be 'approved' before sprint creation
    """
    
    __tablename__ = "sprints"

    # Name
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # FK to Project
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Sprint goal
    goal: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Dates
    start_date: Mapped[date | None] = mapped_column(Text, nullable=True)  # Stored as ISO string
    end_date: Mapped[date | None] = mapped_column(Text, nullable=True)
    
    # Capacity in hours
    capacity_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=SprintStatus.PLANNING.value,
    )
    
    # Override path depth
    path_depth: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    
    def __repr__(self) -> str:
        return f"<Sprint(id={self.id}, name={self.name}, status={self.status})>"