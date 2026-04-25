"""Task queue with atomic checkout.

ORCH-01: Heartbeat-based task assignment - agents check for eligible tasks.
ORCH-04: Execution Agents execute autonomously within approved scope.
Implements: Task checkout with atomic locks (no double-work).
"""

import enum
from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import Column, DateTime, String, JSON
from sqlalchemy.orm import Session

from ethos_os.db import Base


class TaskLockStatus(enum.Enum):
    """Task lock status."""
    AVAILABLE = "available"
    CHECKED_OUT = "checked_out"
    COMPLETE = "complete"
    RELEASED = "released"


class TaskLock(Base):
    """Atomic lock for task checkout.

    Prevents double-work by ensuring only one agent can claim a task.
    """

    __tablename__ = "task_locks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    task_id = Column(String(36), nullable=False, unique=True, index=True)
    agent_id = Column(String(36), nullable=True, index=True)
    status = Column(String(20), nullable=False, default=TaskLockStatus.AVAILABLE.value)
    checked_out_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    task_metadata = Column(JSON, nullable=True)

    def is_expired(self) -> bool:
        """Check if lock has expired."""
        if self.status == TaskLockStatus.CHECKED_OUT.value and self.expires_at:
            return datetime.now() > self.expires_at
        return False

    def __repr__(self) -> str:
        return f"<TaskLock(task={self.task_id}, agent={self.agent_id}, status={self.status})>"


class TaskQueue:
    """Task queue with atomic checkout.

    Requirements:
    - ORCH-01: Heartbeat-based task assignment
    - Atomic locks prevent double-work
    - Configurable lock timeout
    """

    def __init__(self, session: Session, lock_timeout_seconds: int = 300):
        self.session = session
        self.lock_timeout_seconds = lock_timeout_seconds

    def checkout(
        self,
        task_id: str,
        agent_id: str,
    ) -> bool:
        """Atomically checkout a task for an agent.

        Returns True if checkout successful, False if already claimed.
        """
        lock = self._get_or_create_lock(task_id)

        if lock.status == TaskLockStatus.CHECKED_OUT.value:
            if lock.agent_id == agent_id:
                return True
            return False

        if lock.status == TaskLockStatus.AVAILABLE.value:
            lock.agent_id = agent_id
            lock.status = TaskLockStatus.CHECKED_OUT.value
            lock.checked_out_at = datetime.now()

            expires = datetime.now().timestamp() + self.lock_timeout_seconds
            lock.expires_at = datetime.fromtimestamp(expires)

            self.session.flush()
            return True

        return False

    def release(
        self,
        task_id: str,
        agent_id: str,
    ) -> bool:
        """Release a task lock.

        Returns True if released, False if not owned by agent.
        """
        lock = self._get_or_create_lock(task_id)

        if lock.agent_id != agent_id:
            return False

        lock.status = TaskLockStatus.RELEASED.value
        lock.agent_id = None
        lock.checked_out_at = None
        lock.expires_at = None

        self.session.flush()
        return True

    def complete(
        self,
        task_id: str,
        agent_id: str,
    ) -> bool:
        """Mark task as complete (releases lock).

        Returns True if completed, False if not owned by agent.
        """
        lock = self._get_or_create_lock(task_id)

        if lock.agent_id != agent_id:
            return False

        lock.status = TaskLockStatus.COMPLETE.value
        lock.agent_id = None

        self.session.flush()
        return True

    def get_eligible_tasks(
        self,
        agent_id: str,
        limit: int = 10,
    ) -> list[dict]:
        """Get tasks eligible for checkout by an agent.

        Returns tasks that are available or owned by this agent.
        """
        from ethos_os.models.task import Task, TaskStatus

        stmt = (
            select(Task)
            .where(Task.assignee_id == agent_id)
            .where(Task.status != TaskStatus.DONE.value)
            .order_by(Task.created_at)
            .limit(limit)
        )

        tasks = list(self.session.execute(stmt).scalars().all())

        result = []
        for task in tasks:
            lock = self._get_or_create_lock(task.id)
            if lock.status in [
                TaskLockStatus.AVAILABLE.value,
                TaskLockStatus.CHECKED_OUT.value,
            ]:
                if (
                    lock.status == TaskLockStatus.CHECKED_OUT.value
                    and lock.agent_id != agent_id
                ):
                    continue

                result.append({
                    "task_id": task.id,
                    "task_name": task.name,
                    "status": task.status,
                    "lock_status": lock.status,
                    "checked_out_at": lock.checked_out_at.isoformat() if lock.checked_out_at else None,
                })

        return result

    def _get_or_create_lock(self, task_id: str) -> TaskLock:
        """Get or create a task lock."""
        lock = self.session.query(TaskLock).where(TaskLock.task_id == task_id).first()

        if not lock:
            lock = TaskLock(
                id=str(uuid4()),
                task_id=task_id,
                status=TaskLockStatus.AVAILABLE.value,
            )
            self.session.add(lock)
            self.session.flush()

        return lock

    def refresh_lock(self, task_id: str, agent_id: str) -> bool:
        """Refresh lock expiration (heartbeat).

        Returns True if refreshed, False otherwise.
        """
        lock = self._get_or_create_lock(task_id)

        if lock.agent_id != agent_id:
            return False

        expires = datetime.now().timestamp() + self.lock_timeout_seconds
        lock.expires_at = datetime.fromtimestamp(expires)

        self.session.flush()
        return True


def get_task_queue(session: Session) -> TaskQueue:
    """Get task queue instance."""
    return TaskQueue(session)