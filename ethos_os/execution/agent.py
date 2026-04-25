"""Agent model - registered agents for execution."""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ethos_os.db import Base


class AgentStatus(enum.Enum):
    """Agent execution status."""

    IDLE = "idle"
    WORKING = "working"
    BLOCKED = "blocked"
    COMPLETE = "complete"


class AgentType(enum.Enum):
    """Type of agent."""

    GENERAL = "general"
    SENIOR = "senior"
    SPECIALIST = "specialist"


class Agent(Base):
    """Registered agent for heartbeat execution.

    Requirements:
    - BEAT-01: Agent records heartbeat on configurable interval
    - BEAT-02: Heartbeat includes status
    - BEAT-04: Interval configurable per agent type (min: 10s)
    """

    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    agent_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AgentType.GENERAL.value,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AgentStatus.IDLE.value,
    )

    heartbeat_interval: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=30,
        doc="Interval in seconds between heartbeats"
    )

    last_heartbeat_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of last heartbeat"
    )

    missed_heartbeats: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Consecutive missed heartbeats count"
    )

    current_task_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        doc="Currently assigned task ID"
    )

    capacity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        doc="Number of tasks agent can work on simultaneously"
    )

    @property
    def is_alive(self) -> bool:
        """Check if agent is still alive (has recent heartbeat)."""
        if self.last_heartbeat_at is None:
            return False
        from datetime import timedelta

        threshold = timedelta(seconds=self.heartbeat_interval * 3)
        return datetime.now(self.last_heartbeat_at.tzinfo) < self.last_heartbeat_at + threshold

    @property
    def is_dead(self) -> bool:
        """Check if agent is considered dead."""
        return not self.is_alive

    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, name={self.name}, status={self.status})>"