"""Agent failure handling - lease-not-lock with reassignment."""

import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ethos_os.execution.agent import Agent
from ethos_os.execution.scheduler import AgentRegistry
from ethos_os.models.audit import AuditEventType, AuditLog

logger = logging.getLogger(__name__)


class FailureDetector:
    """Detects agent failures and triggers reassignment.

    Requirements:
    - BEAT-05: Agent failure after N missed heartbeats triggers work reassignment
    """

    def __init__(self, session: Session):
        self.session = session
        self.registry = AgentRegistry(session)
        self.missed_threshold = 3

    def check_for_dead_agents(self) -> list[Agent]:
        """Check for agents that have missed too many heartbeats."""
        agents = self.registry.get_all()
        dead = []
        for agent in agents:
            if agent.missed_heartbeats >= self.missed_threshold:
                dead.append(agent)
        return dead

    def mark_missed_heartbeat(self, agent_id: str) -> int:
        """Mark a missed heartbeat for an agent.
        
        Returns:
            New missed heartbeat count
        """
        return self.registry.increment_missed_heartbeats(agent_id)

    def trigger_reassignment(self, dead_agent: Agent) -> list[str]:
        """Trigger reassignment workflow for a dead agent's tasks.
        
        Returns:
            List of reassigned task IDs
        """
        reassigned_tasks = self._find_tasks_and_reassign(dead_agent.id)
        self._write_reassignment_log(dead_agent.id, reassigned_tasks)
        return reassigned_tasks

    def _find_tasks_and_reassign(self, agent_id: str) -> list[str]:
        """Find tasks assigned to agent and reassign them."""
        from ethos_os.models.task import Task, TaskStatus

        stmt = select(Task).where(Task.assignee_id == agent_id)
        tasks = list(self.session.execute(stmt).scalars().all())

        reassigned = []
        for task in tasks:
            if task.status != TaskStatus.DONE.value:
                task.assignee_id = None
                task.status = TaskStatus.BLOCKED.value
                reassigned.append(task.id)

        self.session.flush()
        return reassigned

    def _write_reassignment_log(
        self,
        agent_id: str,
        reassigned_tasks: list[str],
    ) -> None:
        """Write reassignment event to audit log."""
        import json
        from uuid import uuid4

        stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(1)
        last_record = self.session.execute(stmt).scalar_one_or_none()

        payload = json.dumps({
            "dead_agent_id": agent_id,
            "reassigned_tasks": reassigned_tasks,
            "reason": "missed_heartbeats",
        })
        timestamp = datetime.now()

        previous_hash = last_record.hash if last_record else None
        record_hash = AuditLog.compute_hash(previous_hash, payload, timestamp)

        audit_record = AuditLog(
            id=str(uuid4()),
            event_type=AuditEventType.TASK_BLOCKED.value,
            entity_id=agent_id,
            entity_type="agent",
            payload=payload,
            previous_hash=previous_hash,
            hash=record_hash,
            timestamp=timestamp,
        )
        self.session.add(audit_record)
        self.session.flush()
        logger.warning(
            f"Agent {agent_id} marked dead, {len(reassigned_tasks)} tasks reassigned"
        )

    def find_agent_with_capacity(self) -> Agent | None:
        """Find an agent with available capacity."""
        agents = self.registry.get_all()
        for agent in agents:
            if agent.capacity > 0:
                return agent
        return None