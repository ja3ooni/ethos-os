"""Heartbeat record model - agent heartbeat events."""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String, Text
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from ethos_os.db import Base


class Heartbeat(Base):
    """Heartbeat record for agent status updates.

    Requirements:
    - BEAT-02: Heartbeat record includes: timestamp, agent_id, status, task_id, progress_note
    - BEAT-07: Dashboard shows heartbeat timeline per agent
    """

    __tablename__ = "heartbeats"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    agent_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    task_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        doc="Task being worked on"
    )

    progress_note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Progress update text"
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    @property
    def payload_data(self) -> dict[str, Any]:
        """Get heartbeat payload as dict."""
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "task_id": self.task_id,
            "progress_note": self.progress_note,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

    def __repr__(self) -> str:
        return f"<Heartbeat(agent={self.agent_id}, status={self.status})>"