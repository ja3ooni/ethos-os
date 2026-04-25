"""Agent executor - gate-aware execution loop."""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from ethos_os.execution.agent import AgentStatus
from ethos_os.execution.scheduler import AgentRegistry
from ethos_os.models.audit import AuditEventType, AuditLog
from ethos_os.models.task import Task, TaskStatus
from ethos_os.repositories.gate import GateRepository

logger = logging.getLogger(__name__)


class ExecutionResult:
    """Result of an execution cycle."""

    def __init__(
        self,
        task_executed: bool,
        task_id: str | None,
        blocked: bool,
        reason: str | None,
    ):
        self.task_executed = task_executed
        self.task_id = task_id
        self.blocked = blocked
        self.reason = reason


class AgentExecutor:
    """Gate-aware agent execution loop.

    Requirements:
    - BEAT-03: Agent heartbeat loop: check tasks → check gates → execute eligible → update working memory → write episodic log → report
    - BEAT-06: Agent cannot execute gated work
    """

    def __init__(self, session: Session):
        self.session = session
        self.gate_repo = GateRepository(session)
        self.registry = AgentRegistry(session)

    def get_assigned_tasks(self, agent_id: str) -> list[Task]:
        """Get tasks assigned to an agent."""
        stmt = (
            select(Task)
            .where(Task.assignee_id == agent_id)
            .where(Task.status != TaskStatus.DONE.value)
            .order_by(Task.created_at)
        )
        return list(self.session.execute(stmt).scalars().all())

    def check_gate_status(self, task_id: str) -> tuple[bool, str | None]:
        """Check if task has pending gates.
        
        Returns:
            (is_blocked, reason)
        """
        pending = self.gate_repo.get_pending_for_entity(task_id)
        if pending:
            return True, f"Pending {len(pending)} gate(s)"
        return False, None

    def execute_cycle(self, agent_id: str, progress_note: str | None = None) -> ExecutionResult:
        """Execute one heartbeat cycle for an agent.
        
        Steps:
        1. Check assigned tasks
        2. Check gate status for each task
        3. Execute eligible task
        4. Update working memory
        5. Write episodic log
        6. Report
        """
        agent = self.registry.get(agent_id)
        if agent is None:
            raise KeyError(f"Agent not found: {agent_id}")

        tasks = self.get_assigned_tasks(agent_id)

        if not tasks:
            self.registry.update_status(agent_id, AgentStatus.IDLE.value)
            return ExecutionResult(
                task_executed=False,
                task_id=None,
                blocked=False,
                reason="No assigned tasks",
            )

        for task in tasks:
            is_blocked, reason = self.check_gate_status(task.id)
            if is_blocked:
                self.registry.update_status(
                    agent_id,
                    AgentStatus.BLOCKED.value,
                    task.id,
                )
                self._write_blocked_log(agent_id, task.id, reason)
                return ExecutionResult(
                    task_executed=False,
                    task_id=task.id,
                    blocked=True,
                    reason=reason,
                )

            return self._execute_task(agent_id, task, progress_note)

        return ExecutionResult(
            task_executed=False,
            task_id=None,
            blocked=False,
            reason="All tasks checked",
        )

    def _execute_task(
        self,
        agent_id: str,
        task: Task,
        progress_note: str | None,
    ) -> ExecutionResult:
        """Execute a single task."""
        if task.status == TaskStatus.TODO.value:
            task.status = TaskStatus.IN_PROGRESS.value

        self.registry.update_status(
            agent_id,
            AgentStatus.WORKING.value,
            task.id,
        )

        self._write_execution_log(agent_id, task.id, progress_note)

        return ExecutionResult(
            task_executed=True,
            task_id=task.id,
            blocked=False,
            reason=None,
        )

    def _write_blocked_log(self, agent_id: str, task_id: str, reason: str) -> None:
        """Write blocked event to audit log."""
        import json
        from datetime import datetime
        from uuid import uuid4

        stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(1)
        last_record = self.session.execute(stmt).scalar_one_or_none()

        payload = json.dumps({
            "agent_id": agent_id,
            "task_id": task_id,
            "reason": reason,
        })
        timestamp = datetime.now()

        previous_hash = last_record.hash if last_record else None
        record_hash = AuditLog.compute_hash(previous_hash, payload, timestamp)

        audit_record = AuditLog(
            id=str(uuid4()),
            event_type=AuditEventType.TASK_BLOCKED.value,
            entity_id=task_id,
            entity_type="task",
            payload=payload,
            previous_hash=previous_hash,
            hash=record_hash,
            timestamp=timestamp,
        )
        self.session.add(audit_record)
        self.session.flush()

    def _write_execution_log(
        self,
        agent_id: str,
        task_id: str,
        progress_note: str | None,
    ) -> None:
        """Write execution event to audit log."""
        import json
        from datetime import datetime
        from uuid import uuid4

        stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(1)
        last_record = self.session.execute(stmt).scalar_one_or_none()

        payload = json.dumps({
            "agent_id": agent_id,
            "task_id": task_id,
            "progress_note": progress_note,
        })
        timestamp = datetime.now()

        previous_hash = last_record.hash if last_record else None
        record_hash = AuditLog.compute_hash(previous_hash, payload, timestamp)

        audit_record = AuditLog(
            id=str(uuid4()),
            event_type=AuditEventType.HEARTBEAT.value,
            entity_id=agent_id,
            entity_type="agent",
            payload=payload,
            previous_hash=previous_hash,
            hash=record_hash,
            timestamp=timestamp,
        )
        self.session.add(audit_record)
        self.session.flush()

    def can_execute_task(self, task_id: str) -> bool:
        """Check if a task can be executed (no pending gates)."""
        return not self.gate_repo.has_pending_gate(task_id)