"""Task router - matches tasks to capable agents.

ORCH-02: Capability matching - route tasks to agents with matching capabilities.
Strategy: Select cheapest capable agent first.
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ethos_os.agents.registry import Agent, AgentRepository
from ethos_os.models.task import Task, TaskStatus


class TaskRouter:
    """Routes tasks to capable agents based on capability matching.

    Requirements:
    - ORCH-02: Capability matching
    - Route to cheapest capable agent first
    """

    def __init__(self, session: Session):
        self.session = session
        self.agent_repo = AgentRepository(session)

    def match_task_to_agents(
        self,
        task_id: str,
        required_capabilities: list[str] | None = None,
        preferred_role: str | None = None,
        preferred_division: str | None = None,
    ) -> list[dict]:
        """Match task to capable agents.

        Returns agents sorted by cost (cheapest first).
        """
        task = self.session.get(Task, task_id)
        if not task:
            return []

        candidates = self.agent_repo.list_for_task(
            role=preferred_role,
            division=preferred_division,
            capabilities=required_capabilities,
            hired_only=True,
            limit=20,
        )

        sorted_agents = sorted(
            candidates,
            key=lambda a: float(a.get("cost_per_call_usd", "0.01")),
        )

        return sorted_agents

    def assign_best_agent(
        self,
        task_id: str,
        required_capabilities: list[str] | None = None,
        preferred_role: str | None = None,
        preferred_division: str | None = None,
    ) -> str | None:
        """Assign the best (cheapest capable) agent to a task.

        Returns agent_id or None if no capable agent found.
        """
        candidates = self.match_task_to_agents(
            task_id,
            required_capabilities,
            preferred_role,
            preferred_division,
        )

        if not candidates:
            return None

        best_agent = candidates[0]
        agent_id = best_agent["id"]

        task = self.session.get(Task, task_id)
        if task:
            task.assignee_id = agent_id
            self.session.flush()

        return agent_id

    def get_agent_capacity(self, agent_id: str) -> int:
        """Get agent's current workload (active tasks)."""
        stmt = (
            select(Task)
            .where(Task.assignee_id == agent_id)
            .where(Task.status != TaskStatus.DONE.value)
        )
        return len(list(self.session.execute(stmt).scalars().all()))

    def find_available_agent(
        self,
        role: str | None = None,
        division: str | None = None,
        capabilities: list[str] | None = None,
    ) -> Agent | None:
        """Find an agent with available capacity.

        Returns first available agent (by cost) or None.
        """
        candidates = self.agent_repo.list_for_task(
            role=role,
            division=division,
            capabilities=capabilities,
            hired_only=True,
            limit=50,
        )

        for candidate in candidates:
            agent_id = candidate["id"]
            capacity = self.get_agent_capacity(agent_id)

            agent = self.session.get(Agent, agent_id)
            if agent and capacity < (getattr(agent, "capacity", 1) or 1):
                return agent

        return None


def get_task_router(session: Session) -> TaskRouter:
    """Get task router instance."""
    return TaskRouter(session)