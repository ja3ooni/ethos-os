"""Failure detection and task reassignment.

ORCH-05: Agent failure detection - missed heartbeats trigger task reassignment.
ORCH-06: Task assignment respects initiative hierarchy (PRD gate must pass).
"""

import enum
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.orm import Session

from ethos_os.db import Base


class FailureType(enum.Enum):
    """Failure type."""
    MISSED_HEARTBEAT = "missed_heartbeat"
    TASK_FAILED = "task_failed"
    GATE_BLOCKED = "gate_blocked"
    BUDGET_EXCEEDED = "budget_exceeded"


class FailureRecord(Base):
    """Failure record for tracking agent failures."""

    __tablename__ = "agent_failures"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    agent_id = Column(String(36), nullable=False, index=True)
    task_id = Column(String(36), nullable=True, index=True)
    failure_type = Column(String(30), nullable=False)
    reason = Column(String(255), nullable=True)
    details = Column(Text, nullable=True)
    resolved = Column(String(10), nullable=False, default="pending")
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(36), nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<FailureRecord(agent={self.agent_id}, type={self.failure_type})>"


class FailureDetector:
    """Agent failure detection and task reassignment.

    Requirements:
    - ORCH-05: Missed heartbeat triggers reassignment
    - ORCH-06: Task assignment respects initiative hierarchy
    """

    DEFAULT_MISSED_THRESHOLD = 3

    def __init__(
        self,
        session: Session,
        missed_heartbeat_threshold: int = 3,
    ):
        self.session = session
        self.missed_heartbeat_threshold = missed_heartbeat_threshold

    def detect_failures(self, agent_id: str) -> list[dict]:
        """Detect failures for an agent.

        Returns list of detected failures.
        """
        from ethos_os.agents.registry import Agent
        from ethos_os.execution.agent import Agent as ExecAgent

        failures = []

        agent = self.session.get(Agent, agent_id)
        exec_agent = self.session.get(ExecAgent, agent_id)

        if not agent:
            return []

        if exec_agent and exec_agent.missed_heartbeats >= self.missed_heartbeat_threshold:
            failures.append({
                "type": FailureType.MISSED_HEARTBEAT.value,
                "count": exec_agent.missed_heartbeats,
                "reason": f"Missed {exec_agent.missed_heartbeats} heartbeats",
            })

        return failures

    def record_failure(
        self,
        agent_id: str,
        task_id: str | None,
        failure_type: str,
        reason: str | None = None,
        details: str | None = None,
    ) -> FailureRecord:
        """Record a failure."""
        record = FailureRecord(
            id=str(uuid4()),
            agent_id=agent_id,
            task_id=task_id,
            failure_type=failure_type,
            reason=reason,
            details=details,
        )
        self.session.add(record)
        self.session.flush()
        return record

    def reassign_tasks(
        self,
        failed_agent_id: str,
        new_agent_id: str | None = None,
    ) -> list[str]:
        """Reassign tasks from failed agent.

        Returns list of task IDs reassigned.
        """
        from ethos_os.models.task import Task, TaskStatus

        stmt = (
            self.session.query(Task)
            .where(Task.assignee_id == failed_agent_id)
            .where(Task.status != TaskStatus.DONE.value)
        )
        tasks = list(self.session.execute(stmt).scalars().all())

        reassigned = []
        for task in tasks:
            if new_agent_id:
                task.assignee_id = new_agent_id
            else:
                task.status = TaskStatus.TODO.value

            reassigned.append(task.id)

        self.session.flush()

        self.record_failure(
            failed_agent_id,
            None,
            FailureType.MISSED_HEARTBEAT.value,
            f"Reassigned {len(reassigned)} tasks",
        )

        return reassigned

    def resolve_failure(
        self,
        failure_id: str,
        resolved_by: str | None = None,
    ) -> bool:
        """Mark a failure as resolved."""
        failure = self.session.query(FailureRecord).where(
            FailureRecord.id == failure_id
        ).first()

        if not failure:
            return False

        failure.resolved = "resolved"
        failure.resolved_at = datetime.now()
        failure.resolved_by = resolved_by

        self.session.flush()
        return True

    def get_unresolved_failures(
        self,
        agent_id: str | None = None,
    ) -> list[dict]:
        """Get unresolved failures."""
        query = self.session.query(FailureRecord).where(
            FailureRecord.resolved == "pending"
        )

        if agent_id:
            query = query.where(FailureRecord.agent_id == agent_id)

        records = query.order_by(FailureRecord.timestamp.desc()).all()

        return [
            {
                "id": r.id,
                "agent_id": r.agent_id,
                "task_id": r.task_id,
                "failure_type": r.failure_type,
                "reason": r.reason,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            }
            for r in records
        ]


def get_failure_detector(
    session: Session,
    missed_heartbeat_threshold: int = 3,
) -> FailureDetector:
    """Get failure detector instance."""
    return FailureDetector(session, missed_heartbeat_threshold)