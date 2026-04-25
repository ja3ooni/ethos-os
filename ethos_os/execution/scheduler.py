"""Heartbeat scheduler - orchestrates agent heartbeats."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from ethos_os.execution.agent import Agent, AgentStatus
from ethos_os.execution.heartbeat import Heartbeat
from ethos_os.models.audit import AuditEventType, AuditLog
from ethos_os.config import get_settings

logger = logging.getLogger(__name__)


class HeartbeatScheduler:
    """Asyncio-based heartbeat scheduler for agents.

    Requirements:
    - BEAT-01: Agent records heartbeat on configurable interval
    - BEAT-02: Heartbeat includes status
    - BEAT-04: Interval configurable per agent type (min: 10s)
    """

    def __init__(self, session: Session):
        self.session = session
        self.settings = get_settings()
        self._running_tasks: dict[str, asyncio.Task] = {}
        self._heartbeat_callbacks: list[Callable] = []

    def register_callback(self, callback: Callable) -> None:
        """Register a callback to be called on each heartbeat."""
        self._heartbeat_callbacks.append(callback)

    async def start_agent(
        self,
        agent_id: str,
        interval_seconds: int | None = None,
    ) -> None:
        """Start heartbeat loop for an agent."""

        agent = self.session.get(Agent, agent_id)
        if agent is None:
            raise KeyError(f"Agent not found: {agent_id}")

        interval = interval_seconds or agent.heartbeat_interval
        interval = max(interval, 10)

        task = asyncio.create_task(
            self._heartbeat_loop(agent_id, interval),
            name=f"heartbeat-{agent_id}",
        )
        self._running_tasks[agent_id] = task
        logger.info(f"Started heartbeat loop for agent {agent_id}")

    async def stop_agent(self, agent_id: str) -> None:
        """Stop heartbeat loop for an agent."""
        task = self._running_tasks.pop(agent_id, None)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            logger.info(f"Stopped heartbeat loop for agent {agent_id}")

    async def stop_all(self) -> None:
        """Stop all heartbeat loops."""
        for agent_id in list(self._running_tasks.keys()):
            await self.stop_agent(agent_id)

    async def _heartbeat_loop(self, agent_id: str, interval: int) -> None:
        """Heartbeat loop for a single agent."""
        while True:
            try:
                await asyncio.sleep(interval)
                await self._emit_heartbeat(agent_id)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop for {agent_id}: {e}")

    async def _emit_heartbeat(self, agent_id: str) -> None:
        """Emit a heartbeat and call registered callbacks."""
        from uuid import uuid4

        agent = self.session.get(Agent, agent_id)
        if agent is None:
            logger.warning(f"Agent {agent_id} not found, stopping heartbeat")
            await self.stop_agent(agent_id)
            return

        last_status = self._get_last_status(agent_id)
        should_log = agent.status != last_status

        if agent.status == AgentStatus.IDLE.value and last_status == AgentStatus.IDLE.value:
            should_log = False

        now = datetime.now()
        if should_log or last_status is None:
            heartbeat = Heartbeat(
                id=str(uuid4()),
                agent_id=agent_id,
                status=agent.status,
                task_id=agent.current_task_id,
                progress_note=None,
            )
            self.session.add(heartbeat)
            self.session.flush()
            self._write_audit_log(agent_id, heartbeat)

        agent.last_heartbeat_at = now
        agent.missed_heartbeats = 0
        self.session.flush()

        for callback in self._heartbeat_callbacks:
            try:
                callback(agent_id, agent.status)
            except Exception as e:
                logger.error(f"Error in heartbeat callback: {e}")

    def _get_last_status(self, agent_id: str) -> str | None:
        """Get the last recorded status for an agent."""
        stmt = (
            select(Heartbeat)
            .where(Heartbeat.agent_id == agent_id)
            .order_by(Heartbeat.timestamp.desc())
            .limit(1)
        )
        result = self.session.execute(stmt).scalar_one_or_none()
        return result.status if result else None

    def _write_audit_log(self, agent_id: str, heartbeat: Heartbeat) -> None:
        """Write heartbeat to episodic audit log."""
        from uuid import uuid4

        stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(1)
        last_record = self.session.execute(stmt).scalar_one_or_none()

        payload = json.dumps(heartbeat.payload_data)
        timestamp = heartbeat.timestamp or datetime.now()

        previous_hash = last_record.hash if last_record else None
        record_hash = AuditLog.compute_hash(
            previous_hash,
            payload,
            timestamp,
        )

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

    def get_agent_heartbeats(
        self,
        agent_id: str,
        limit: int = 100,
    ) -> list[Heartbeat]:
        """Get heartbeat timeline for an agent."""
        stmt = (
            select(Heartbeat)
            .where(Heartbeat.agent_id == agent_id)
            .order_by(Heartbeat.timestamp.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())


class AgentRegistry:
    """Registry for managing agent registrations."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        agent_id: str,
        name: str,
        agent_type: str = "general",
        heartbeat_interval: int = 30,
        capacity: int = 1,
    ) -> Agent:
        """Register a new agent."""

        if heartbeat_interval < 10:
            heartbeat_interval = 10

        agent = Agent(
            id=agent_id,
            name=name,
            agent_type=agent_type,
            status=AgentStatus.IDLE.value,
            heartbeat_interval=heartbeat_interval,
            capacity=capacity,
        )
        self.session.add(agent)
        self.session.flush()
        return agent

    def get(self, agent_id: str) -> Agent | None:
        """Get an agent by ID."""
        return self.session.get(Agent, agent_id)

    def get_all(self) -> list[Agent]:
        """Get all registered agents."""
        stmt = select(Agent).order_by(Agent.name)
        return list(self.session.execute(stmt).scalars().all())

    def update_status(
        self,
        agent_id: str,
        status: str,
        task_id: str | None = None,
    ) -> Agent:
        """Update agent status."""
        agent = self.get(agent_id)
        if agent is None:
            raise KeyError(f"Agent not found: {agent_id}")

        agent.status = status
        if task_id is not None:
            agent.current_task_id = task_id
        self.session.flush()
        return agent

    def increment_missed_heartbeats(self, agent_id: str) -> int:
        """Increment missed heartbeat count and return new count."""
        agent = self.get(agent_id)
        if agent is None:
            return 0

        agent.missed_heartbeats += 1
        self.session.flush()
        return agent.missed_heartbeats

    def get_dead_agents(self) -> list[Agent]:
        """Get agents that are considered dead (missed too many heartbeats)."""
        stmt = select(Agent).where(Agent.missed_heartbeats >= 3)
        return list(self.session.execute(stmt).scalars().all())