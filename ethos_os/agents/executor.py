"""Agent execution engine - token-efficient.

Design: Don't dump everything into context.
- Fetch agent config only when executing
- Cache in working memory (1hr TTL)
- Use reference IDs until execution time
"""

from datetime import datetime
from typing import Any
from uuid import uuid4

from ethos_os.memory.working import get_working_memory
from ethos_os.agents.registry import AgentRepository, get_agent_repository


class AgentExecutor:
    """Token-efficient agent execution.

    Strategy:
    1. Agent selection: Use registry listing (summary only, no full prompts)
    2. Agent execution: Fetch full config, cache in working memory
    3. Task execution: Inject only current context, not full history
    4. Memory: Vector store for long context, SQLite for state
    """

    def __init__(self):
        self.repo = get_agent_repository()
        self.working_memory = get_working_memory()

    def list_agents_for_task(
        self,
        task_requirements: list[str],
        role: str | None = None,
        division: str | None = None,
    ) -> list[dict]:
        """List agents suitable for a task - TOKEN EFFICIENT.

        Returns only summaries, not full prompts.
        Use this for UI listings and agent selection.
        """
        return self.repo.list_for_task(
            role=role,
            division=division,
            capabilities=task_requirements,
            hired_only=True,
        )

    def select_agent(self, agent_id: str) -> dict | None:
        """Select agent and prepare for execution.

        Fetches full config but caches in working memory.
        Next executions reuse cached config.
        """
        # Check working memory cache
        cache_key = f"agent:{agent_id}:config"
        cached = self.working_memory.get("system", cache_key)

        if cached:
            return cached

        # Fetch from registry (only at execution time)
        config = self.repo.get_for_execution(agent_id)
        if not config:
            return None

        # Cache in working memory (1 hour TTL)
        self.working_memory.set(
            "system",
            cache_key,
            config,
            ttl_seconds=3600,
        )

        # Update usage tracking
        self.repo.update_last_used(agent_id)

        return config

    def execute_task(
        self,
        agent_id: str,
        task_prompt: str,
        context: dict[str, Any] | None = None,
    ) -> dict:
        """Execute a task with agent - TOKEN EFFICIENT.

        Only injects:
        - Agent summary (from cache)
        - Current task prompt
        - Relevant context (not full history)
        - Initiative link (what project/sprint)
        """
        agent_config = self.select_agent(agent_id)
        if not agent_config:
            return {"error": "Agent not found or not hired"}

        # Build token-efficient context
        execution_context = self._build_efficient_context(
            agent_config,
            task_prompt,
            context,
        )

        # TODO: Call LLM with execution_context
        # For now, return what would be executed
        return {
            "agent_id": agent_id,
            "agent_name": agent_config["name"],
            "task_prompt": task_prompt,
            "context_size": len(str(execution_context)),
            "would_execute": True,
        }

    def _build_efficient_context(
        self,
        agent_config: dict,
        task_prompt: str,
        context: dict | None,
    ) -> dict:
        """Build context for execution - token efficient.

        Strategy:
        - Include agent summary, NOT full prompt
        - Include only relevant context
        - Reference initiative hierarchy, not dump it
        """
        return {
            "agent": {
                "id": agent_config["id"],
                "name": agent_config["name"],
                "role": agent_config["role"],
                "skills_summary": agent_config["skills_summary"],
                "capabilities": agent_config["capabilities"],
            },
            "task": task_prompt,
            "context": context or {},
            "timestamp": datetime.utcnow().isoformat(),
        }

    def assign_task_to_agent(
        self,
        agent_id: str,
        task_id: str,
        initiative_id: str,
    ) -> dict:
        """Assign a task to an agent for execution.

        Creates heartbeat tracking entry.
        """
        # Update working memory
        self.working_memory.set(
            "system",
            f"task_assignment:{agent_id}:{task_id}",
            {
                "task_id": task_id,
                "initiative_id": initiative_id,
                "assigned_at": datetime.utcnow().isoformat(),
                "status": "assigned",
            },
            ttl_seconds=3600,
        )

        return {
            "agent_id": agent_id,
            "task_id": task_id,
            "status": "assigned",
        }


def get_agent_executor() -> AgentExecutor:
    """Get agent executor instance."""
    return AgentExecutor()