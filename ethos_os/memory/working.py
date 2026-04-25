"""Working memory for EthosOS.

Per-agent in-memory context store (dict + threading.Lock per D-13 through D-17).
Working memory is runtime-only, persists across heartbeat calls in same process
but not across restarts.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
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


@dataclass
class CacheEntry:
    """Cache entry with TTL."""
    value: Any
    expires_at: datetime


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

    # Cache layer for executor - key-value with TTL
    _cache: dict[str, CacheEntry] = {}

    def get(self, prefix: str, key: str) -> Any | None:  # noqa: F811
        """Get cached value - executor interface.
        
        Args:
            prefix: Cache namespace (e.g., "system", "task")
            key: Cache key
            
        Returns:
            Cached value or None if expired/missing
        """
        return self.cache_get(prefix, key)

    def set(self, prefix: str, key: str, value: Any, ttl_seconds: int | None = None) -> None:  # noqa: F811
        """Set cached value - executor interface.
        
        Args:
            prefix: Cache namespace (e.g., "system", "task")
            key: Cache key
            value: Value to cache
            ttl_seconds: TTL in seconds (default: self._ttl_seconds)
        """
        self.cache_set(prefix, key, value, ttl_seconds)

    def cache_get(self, prefix: str, key: str) -> Any | None:
        """Get cached value by prefix + key.
        
        Args:
            prefix: Cache namespace (e.g., "system", "task")
            key: Cache key
            
        Returns:
            Cached value or None if expired/missing
        """
        cache_key = f"{prefix}:{key}"
        with self._lock:
            entry = self._cache.get(cache_key)
            if entry is None:
                return None
            if entry.expires_at < datetime.utcnow():
                del self._cache[cache_key]
                return None
            return entry.value

    def cache_set(self, prefix: str, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        """Set cached value with TTL.
        
        Args:
            prefix: Cache namespace (e.g., "system", "task")
            key: Cache key
            value: Value to cache
            ttl_seconds: TTL in seconds (default: self._ttl_seconds)
        """
        cache_key = f"{prefix}:{key}"
        ttl = ttl_seconds or self._ttl_seconds
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        
        with self._lock:
            self._cache[cache_key] = CacheEntry(value=value, expires_at=expires_at)

    def cache_delete(self, prefix: str, key: str) -> bool:
        """Delete cached value.
        
        Args:
            prefix: Cache namespace
            key: Cache key
            
        Returns:
            True if deleted, False if not found
        """
        cache_key = f"{prefix}:{key}"
        with self._lock:
            if cache_key in self._cache:
                del self._cache[cache_key]
                return True
            return False

    def cache_clear_prefix(self, prefix: str) -> int:
        """Clear all cached values for a prefix.
        
        Args:
            prefix: Cache namespace to clear
            
        Returns:
            Number of entries cleared
        """
        cleared = 0
        with self._lock:
            to_delete = [k for k in self._cache if k.startswith(f"{prefix}:")]
            for k in to_delete:
                del self._cache[k]
                cleared += 1
        return cleared


# Singleton instance for get_working_memory()
_working_memory_instance: WorkingMemory | None = None


def get_working_memory() -> WorkingMemory:
    """Get singleton WorkingMemory instance."""
    global _working_memory_instance
    if _working_memory_instance is None:
        _working_memory_instance = WorkingMemory()
    return _working_memory_instance