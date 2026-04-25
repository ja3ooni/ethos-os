"""Working memory for EthosOS.

Per-agent in-memory context store (dict + threading.Lock per D-13 through D-17).
Working memory is runtime-only, persists across heartbeat calls in same process
but not across restarts.
"""

from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Any
from uuid import uuid4


@dataclass
class AgentContext:
    """Context for a single agent in working memory."""
    
    task_context: str | None = None
    reasoning_state: dict = field(default_factory=dict)
    subtask_decomposition: list = field(default_factory=list)
    short_term_refs: dict = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.utcnow)


class WorkingMemory:
    """Per-agent working memory with thread-safe access."""
    
    def __init__(self, ttl_seconds: int = 3600):
        """Initialize working memory.
        
        Args:
            ttl_seconds: Time-to-live for inactive agents (default: 1 hour)
        """
        self._store: dict[str, AgentContext] = {}
        self._lock = Lock()
        self._ttl_seconds = ttl_seconds
    
    def register(self, agent_id: str | None = None) -> str:
        """Register a new agent.
        
        Args:
            agent_id: Optional agent ID (generated if not provided)
        
        Returns:
            Agent ID
        """
        with self._lock:
            if agent_id is None:
                agent_id = str(uuid4())
            
            if agent_id not in self._store:
                self._store[agent_id] = AgentContext()
            
            return agent_id
    
    def get(self, agent_id: str) -> AgentContext | None:
        """Get agent context.
        
        Args:
            agent_id: Agent ID
        
        Returns:
            AgentContext or None if not found
        """
        with self._lock:
            return self._store.get(agent_id)
    
    def set(self, agent_id: str, context: AgentContext) -> None:
        """Set agent context.
        
        Args:
            agent_id: Agent ID
            context: AgentContext to store
        """
        with self._lock:
            # Update last_updated
            context.last_updated = datetime.utcnow()
            self._store[agent_id] = context
    
    def update(self, agent_id: str, **kwargs: Any) -> None:
        """Update specific fields in agent context.
        
        Args:
            agent_id: Agent ID
            **kwargs: Fields to update (task_context, reasoning_state, etc.)
        """
        with self._lock:
            if agent_id not in self._store:
                self._store[agent_id] = AgentContext()
            
            context = self._store[agent_id]
            
            if "task_context" in kwargs:
                context.task_context = kwargs["task_context"]
            if "reasoning_state" in kwargs:
                context.reasoning_state = kwargs["reasoning_state"]
            if "subtask_decomposition" in kwargs:
                context.subtask_decomposition = kwargs["subtask_decomposition"]
            if "short_term_refs" in kwargs:
                context.short_term_refs = kwargs["short_term_refs"]
            
            context.last_updated = datetime.utcnow()
    
    def clear(self, agent_id: str) -> bool:
        """Clear agent context.
        
        Args:
            agent_id: Agent ID
        
        Returns:
            True if agent was removed
        """
        with self._lock:
            if agent_id in self._store:
                del self._store[agent_id]
                return True
            return False
    
    def get_agent_context(self, agent_id: str) -> AgentContext | None:
        """Get agent context (alias for get).
        
        Args:
            agent_id: Agent ID
        
        Returns:
            AgentContext or None
        """
        return self.get(agent_id)
    
    def list_agents(self) -> list[str]:
        """List registered agent IDs.
        
        Returns:
            List of agent IDs
        """
        with self._lock:
            return list(self._store.keys())
    
    def prune_inactive(self, max_age_seconds: int | None = None) -> int:
        """Remove agents inactive beyond TTL.
        
        Args:
            max_age_seconds: Max age in seconds (default: self._ttl_seconds)
        
        Returns:
            Number of agents removed
        """
        from datetime import timedelta
        
        max_age = max_age_seconds or self._ttl_seconds
        cutoff = datetime.utcnow() - timedelta(seconds=max_age)
        
        removed = 0
        with self._lock:
            for agent_id, context in list(self._store.items()):
                if context.last_updated < cutoff:
                    del self._store[agent_id]
                    removed += 1
        
        return removed
    
    def __len__(self) -> int:
        """Get number of registered agents."""
        with self._lock:
            return len(self._store)