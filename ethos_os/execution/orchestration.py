"""Heartbeat orchestration loop.

Integrates heartbeat with task assignment:
- Check for eligible tasks on each heartbeat
- Check gate status before execution
- Update working memory
- Write episodic log
- Return execution result

Requirements:
- ORCH-01: Heartbeat-based task assignment
- ORCH-04: Execution Agents execute within approved scope
- ORCH-06: Task assignment respects initiative hierarchy (gate must pass)
"""

import json
import logging
from datetime import datetime
from typing import Any, Callable
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from ethos_os.execution.agent import AgentStatus
from ethos_os.execution.scheduler import HeartbeatScheduler
from ethos_os.models.audit import AuditEventType, AuditLog
from ethos_os.models.gate import Gate, GateStatus
from ethos_os.models.task import Task, TaskStatus
from ethos_os.orchestration import (
    get_task_router,
    get_task_queue,
    get_status_tracker,
    get_budget_enforcer,
    get_failure_detector,
)

logger = logging.getLogger(__name__)


class OrchestratedHeartbeat:
    """Heartbeat loop with task orchestration.

    On each heartbeat:
    1. Check assigned tasks
    2. Check gate status
    3. Execute eligible task (with lock)
    4. Update working memory
    5. Write episodic log
    6. Return result
    """

    def __init__(self, session: Session):
        self.session = session
        self.router = get_task_router(session)
        self.queue = get_task_queue(session)
        self.status_tracker = get_status_tracker(session)
        self.budget_enforcer = get_budget_enforcer(session)
        self.failure_detector = get_failure_detector(session)

    def heartbeat_cycle(
        self,
        agent_id: str,
        progress_note: str | None = None,
    ) -> dict[str, Any]:
        """Execute heartbeat cycle for agent with orchestration."""
        from uuid import uuid4

        eligible_tasks = self.queue.get_eligible_tasks(agent_id, limit=1)

        if not eligible_tasks:
            self.status_tracker.transition(
                agent_id, None, AgentStatus.IDLE.value, "No tasks"
            )
            return {
                "agent_id": agent_id,
                "task_executed": False,
                "reason": "No eligible tasks",
            }

        task_data = eligible_tasks[0]
        task_id = task_data["task_id"]

        is_blocked, block_reason = self._check_gates(task_id)
        if is_blocked:
            self.status_tracker.transition(
                agent_id, task_id, AgentStatus.BLOCKED.value, block_reason
            )
            self._write_audit_log(
                agent_id, task_id, "blocked", {"reason": block_reason}
            )
            return {
                "agent_id": agent_id,
                "task_id": task_id,
                "task_executed": False,
                "blocked": True,
                "reason": block_reason,
            }

        checkout_ok = self.queue.checkout(task_id, agent_id)
        if not checkout_ok:
            return {
                "agent_id": agent_id,
                "task_id": task_id,
                "task_executed": False,
                "reason": "Could not checkout (claimed by another)",
            }

        self.queue.refresh_lock(task_id, agent_id)

        self.status_tracker.transition(
            agent_id, task_id, AgentStatus.WORKING.value, progress_note
        )

        if progress_note:
            self._write_audit_log(
                agent_id, task_id, "heartbeat", {"note": progress_note}
            )

        return {
            "agent_id": agent_id,
            "task_id": task_id,
            "task_executed": True,
            "blocked": False,
        }

    def _check_gates(self, entity_id: str) -> tuple[bool, str | None]:
        """Check if entity has pending gates (ORCH-06)."""
        stmt = (
            select(Gate)
            .where(Gate.entity_id == entity_id)
            .where(Gate.status == GateStatus.PENDING.value)
        )
        pending = list(self.session.execute(stmt).scalars().all())
        if pending:
            return True, f"Pending {len(pending)} gate(s)"
        return False, None

    def _write_audit_log(
        self,
        agent_id: str,
        task_id: str | None,
        event_type: str,
        payload: dict,
    ) -> None:
        """Write to audit log."""
        import json
        from uuid import uuid4

        stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(1)
        last_record = self.session.execute(stmt).scalar_one_or_none()

        payload_str = json.dumps({
            "agent_id": agent_id,
            "task_id": task_id,
            **payload,
        })
        timestamp = datetime.now()

        previous_hash = last_record.hash if last_record else None
        record_hash = AuditLog.compute_hash(previous_hash, payload_str, timestamp)

        record = AuditLog(
            id=str(uuid4()),
            event_type=event_type,
            entity_id=agent_id,
            entity_type="agent",
            payload=payload_str,
            previous_hash=previous_hash,
            hash=record_hash,
            timestamp=timestamp,
        )
        self.session.add(record)
        self.session.flush()