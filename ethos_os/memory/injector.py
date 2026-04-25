"""Context injection pipeline for EthosOS agents.

Token-efficient: fetch relevant docs, don't dump everything.
Qdrant for search, working memory for runtime context.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import Lock

from ethos_os.memory.search import ChunkReference, SearchRequest
from ethos_os.memory.working import get_working_memory


DEFAULT_WORKING_MEMORY_TTL = 3600
MAX_INJECTED_TOKENS = 2000


@dataclass
class AgentContextResponse:
    """Context response for agent injection.

    Token-efficient: contains references, not full content.
    """

    chunks: list[ChunkReference]
    total_retrieved: int
    tokens_estimate: int
    from_cache: bool
    search_time_ms: float


@dataclass
class InjectedContext:
    """Context stored in working memory for agent."""

    chunks: list[ChunkReference]
    query: str
    injected_at: datetime
    expires_at: datetime
    initiative_id: str | None = None


class ContextInjector:
    """Inject relevant context into agent prompts.

    Pipeline:
    1. Semantic search via Qdrant
    2. Top-k chunk filtering
    3. Working memory cache with TTL
    4. Reference injection (not full content)
    """

    def __init__(
        self,
        working_memory_ttl: int = DEFAULT_WORKING_MEMORY_TTL,
        max_tokens: int = MAX_INJECTED_TOKENS,
    ):
        """Initialize context injector.

        Args:
            working_memory_ttl: TTL for cached context (seconds)
            max_tokens: Maximum tokens to inject
        """
        self._working_memory_ttl = working_memory_ttl
        self._max_tokens = max_tokens
        self._working_memory = get_working_memory()
        self._cache: dict[str, InjectedContext] = {}
        self._cache_lock = Lock()

    def _get_cache_key(self, agent_id: str, initiative_id: str | None = None) -> str:
        """Generate cache key for agent/initiative."""
        return f"{agent_id}:{initiative_id or 'global'}"

    async def inject(
        self,
        agent_id: str,
        query: str,
        initiative_id: str | None = None,
        initiative_type: str | None = None,
        chunk_types: list[str] | None = None,
        top_k: int = 5,
        min_score: float = 0.7,
        use_cache: bool = True,
    ) -> AgentContextResponse:
        """Inject relevant context into agent.

        Args:
            agent_id: Agent ID for cache key
            query: Search query for semantic search
            initiative_id: Filter by initiative
            initiative_type: Filter by initiative type
            chunk_types: Filter by chunk types
            top_k: Number of chunks to retrieve
            min_score: Minimum relevance score
            use_cache: Whether to check/use cache

        Returns:
            Context response for agent
        """
        start_time = time.time()

        cache_key = self._get_cache_key(agent_id, initiative_id)

        if use_cache:
            cached = self._get_from_cache(cache_key)
            if cached and not self._is_expired(cached):
                return AgentContextResponse(
                    chunks=cached.chunks,
                    total_retrieved=len(cached.chunks),
                    tokens_estimate=sum(c.payload.get("token_count", 0) for c in cached.chunks),
                    from_cache=True,
                    search_time_ms=0,
                )

        from ethos_os.memory.search import get_search_service

        search_service = get_search_service()

        request = SearchRequest(
            query=query,
            initiative_id=initiative_id,
            initiative_type=initiative_type,
            chunk_types=chunk_types,
            top_k=top_k,
            min_score=min_score,
        )

        search_result = await search_service.search(request)

        search_time = (time.time() - start_time) * 1000

        self._store_in_cache(
            cache_key=cache_key,
            context=InjectedContext(
                chunks=search_result.chunks,
                query=query,
                injected_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(seconds=self._working_memory_ttl),
                initiative_id=initiative_id,
            ),
        )

        return AgentContextResponse(
            chunks=search_result.chunks,
            total_retrieved=search_result.total_retrieved,
            tokens_estimate=search_result.tokens_estimate,
            from_cache=False,
            search_time_ms=search_time,
        )

    def _get_from_cache(self, cache_key: str) -> InjectedContext | None:
        """Get context from cache."""
        with self._cache_lock:
            return self._cache.get(cache_key)

    def _is_expired(self, context: InjectedContext) -> bool:
        """Check if context is expired."""
        return datetime.utcnow() > context.expires_at

    def _store_in_cache(self, cache_key: str, context: InjectedContext) -> None:
        """Store context in cache."""
        with self._cache_lock:
            self._cache[cache_key] = context

    def invalidate(self, agent_id: str, initiative_id: str | None = None) -> bool:
        """Invalidate cached context for agent.

        Args:
            agent_id: Agent ID
            initiative_id: Optional initiative ID

        Returns:
            True if cache entry was deleted
        """
        cache_key = self._get_cache_key(agent_id, initiative_id)
        with self._cache_lock:
            if cache_key in self._cache:
                del self._cache[cache_key]
                return True
            return False

    def invalidate_initiative(self, initiative_id: str) -> int:
        """Invalidate all cached contexts for an initiative.

        Args:
            initiative_id: Initiative to invalidate

        Returns:
            Number of entries invalidated
        """
        invalidated = 0
        with self._cache_lock:
            to_delete = [
                key for key, ctx in self._cache.items()
                if ctx.initiative_id == initiative_id
            ]
            for key in to_delete:
                del self._cache[key]
                invalidated += 1
        return invalidated

    def prune_expired(self) -> int:
        """Remove expired cache entries.

        Returns:
            Number of entries removed
        """
        pruned = 0
        with self._cache_lock:
            to_delete = [
                key for key, ctx in self._cache.items()
                if self._is_expired(ctx)
            ]
            for key in to_delete:
                del self._cache[key]
                pruned += 1
        return pruned

    def get_context_for_prompt(
        self,
        agent_id: str,
        query: str,
        initiative_id: str | None = None,
    ) -> str:
        """Get formatted context string for agent prompt.

        Args:
            agent_id: Agent ID
            query: Current query
            initiative_id: Initiative ID

        Returns:
            Formatted context string
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                self.inject(agent_id, query, initiative_id)
            )
        finally:
            loop.close()

        return self._format_for_prompt(result)

    def _format_for_prompt(self, response: AgentContextResponse) -> str:
        """Format context response for agent prompt.

        Token-efficient: references only, not full content.
        """
        if not response.chunks:
            return "No relevant context available."

        lines = ["Relevant context from knowledge base:\n"]

        for i, chunk in enumerate(response.chunks, 1):
            type_indicator = f"[{chunk.chunk_type.upper()}]"
            summary = chunk.summary[:80] + "..." if len(chunk.summary) > 80 else chunk.summary
            lines.append(f"  {i}. {type_indicator} {summary}")

        if response.tokens_estimate > 0:
            lines.append(f"\n  (Retrieved ~{response.tokens_estimate} tokens)")

        if response.from_cache:
            lines.append("  [Cached]")

        return "\n".join(lines)


_injector: ContextInjector | None = None


def get_context_injector() -> ContextInjector:
    """Get singleton context injector."""
    global _injector
    if _injector is None:
        _injector = ContextInjector()
    return _injector