"""Agent status tracker - state machine management.

ORCH-01: Status transitions: idle → working → blocked → complete.
Tracks agent work state per heartbeat.
"""

import enum
from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import Column, DateTime, String, JSON
from sqlalchemy.orm import Session

from ethos_os.db import Base


class AgentWorkStatus(enum.Enum):
    """Agent work status."""
    IDLE = "idle"
    WORKING = "working"
    BLOCKED = "blocked"
    COMPLETE = "complete"


class AgentStatusRecord(Base):
    """Agent status record for tracking work state.

    Records each status transition for audit and dashboard.
    """

    __tablename__ = "agent_status_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    agent_id = Column(String(36), nullable=False, index=True)
    task_id = Column(String(36), nullable=True, index=True)
    previous_status = Column(String(20), nullable=True)
    current_status = Column(String(20), nullable=False)
    reason = Column(String(255), nullable=True)
    status_metadata = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<AgentStatusRecord(agent={self.agent_id}, {self.previous_status}→{self.current_status})>"


class AgentStatusTracker:
    """Agent status state machine.

    Requirements:
    - ORCH-01: Status transitions: idle → working → blocked → complete
    - ORCH-04: Execution Agents execute autonomously
    """

    TRANSITIONS = {
        AgentWorkStatus.IDLE.value: [AgentWorkStatus.WORKING.value],
        AgentWorkStatus.WORKING.value: [
            AgentWorkStatus.BLOCKED.value,
            AgentWorkStatus.COMPLETE.value,
            AgentWorkStatus.IDLE.value,
        ],
        AgentWorkStatus.BLOCKED.value: [
            AgentWorkStatus.WORKING.value,
            AgentWorkStatus.IDLE.value,
        ],
        AgentWorkStatus.COMPLETE.value: [AgentWorkStatus.IDLE.value],
    }

    def __init__(self, session: Session):
        self.session = session

    def transition(
        self,
        agent_id: str,
        task_id: str | None,
        new_status: str,
        reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Transition agent to new status.

        Returns True if transition valid, False otherwise.
        """
        current = self.get_current_status(agent_id)

        if not self._is_valid_transition(current, new_status):
            return False

        record = AgentStatusRecord(
            id=str(uuid4()),
            agent_id=agent_id,
            task_id=task_id,
            previous_status=current,
            current_status=new_status,
            reason=reason,
            metadata=metadata,
        )
        self.session.add(record)
        self.session.flush()

        return True

    def get_current_status(self, agent_id: str) -> str:
        """Get agent's current status."""
        stmt = (
            self.session.query(AgentStatusRecord)
            .where(AgentStatusRecord.agent_id == agent_id)
            .order_by(AgentStatusRecord.timestamp.desc())
            .limit(1)
        )
        record = self.session.execute(stmt).scalar_one_or_none()
        return record.current_status if record else AgentWorkStatus.IDLE.value

    def get_status_history(
        self,
        agent_id: str,
        limit: int = 50,
    ) -> list[dict]:
        """Get agent's status history."""
        stmt = (
            self.session.query(AgentStatusRecord)
            .where(AgentStatusRecord.agent_id == agent_id)
            .order_by(AgentStatusRecord.timestamp.desc())
            .limit(limit)
        )
        records = self.session.execute(stmt).scalars().all()

        return [
            {
                "id": r.id,
                "task_id": r.task_id,
                "previous_status": r.previous_status,
                "current_status": r.current_status,
                "reason": r.reason,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            }
            for r in records
        ]

    def _is_valid_transition(self, from_status: str, to_status: str) -> bool:
        """Check if transition is valid."""
        allowed = self.TRANSITIONS.get(from_status, [])
        return to_status in allowed


def get_status_tracker(session: Session) -> AgentStatusTracker:
    """Get status tracker instance."""
    return AgentStatusTracker(session)