"""Semantic search service for EthosOS vector memory.

Provides token-efficient search with top-k retrieval.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

from ethos_os.memory.collections import CollectionType
from ethos_os.memory.embeddings import encode_text
from ethos_os.memory.qdrant_client import QdrantVectorClient, get_qdrant_client


DEFAULT_TOP_K = 5
DEFAULT_MIN_SCORE = 0.7
MAX_TOP_K = 10


@dataclass
class SearchRequest:
    """Semantic search request."""

    query: str
    initiative_id: str | None = None
    initiative_type: str | None = None
    chunk_types: list[str] | None = None
    collections: list[CollectionType] | None = None
    top_k: int = DEFAULT_TOP_K
    min_score: float = DEFAULT_MIN_SCORE


@dataclass
class ChunkReference:
    """Token-efficient chunk reference for agent injection.

    Contains only summary and metadata, not full content.
    """

    chunk_id: str
    initiative_id: str
    chunk_type: str
    summary: str
    relevance_score: float
    payload: dict[str, Any] = field(default_factory=dict)

    def format_reference(self) -> str:
        """Format as readable reference for agent prompt."""
        return f"[{self.chunk_type}] {self.summary} (relevance: {self.relevance_score:.2f})"


@dataclass
class SearchResult:
    """Search result with chunk references."""

    chunks: list[ChunkReference]
    total_retrieved: int
    tokens_estimate: int
    cached: bool = False
    search_time_ms: float = 0.0

    @property
    def is_empty(self) -> bool:
        """Check if no results found."""
        return len(self.chunks) == 0

    def format_references(self) -> str:
        """Format all references for agent prompt."""
        if not self.chunks:
            return "No relevant context found."

        lines = ["Context from knowledge base:\n"]
        for i, chunk in enumerate(self.chunks, 1):
            lines.append(f"{i}. {chunk.format_reference()}")

        return "\n".join(lines)


class SemanticSearch:
    """Semantic search service for initiative content."""

    def __init__(
        self,
        client: QdrantVectorClient | None = None,
        default_top_k: int = DEFAULT_TOP_K,
        default_min_score: float = DEFAULT_MIN_SCORE,
    ):
        """Initialize search service.

        Args:
            client: Optional Qdrant client
            default_top_k: Default number of results
            default_min_score: Default minimum relevance score
        """
        self._client = client or get_qdrant_client()
        self._default_top_k = min(default_top_k, MAX_TOP_K)
        self._default_min_score = default_min_score

    def _build_filter(self, request: SearchRequest) -> dict[str, Any] | None:
        """Build Qdrant filter conditions."""
        conditions = []

        if request.initiative_id:
            conditions.append({
                "key": "initiative_id",
                "match": {"value": request.initiative_id},
            })

        if request.initiative_type:
            conditions.append({
                "key": "initiative_type",
                "match": {"value": request.initiative_type},
            })

        if request.chunk_types:
            conditions.append({
                "key": "chunk_type",
                "match": {"any": request.chunk_types},
            })

        if not conditions:
            return None

        return {"must": conditions}

    def _build_collections(self, request: SearchRequest) -> list[CollectionType]:
        """Get collections to search."""
        if request.collections:
            return request.collections
        return [CollectionType.PRD, CollectionType.DOCS]

    async def _search_collection(
        self,
        collection: CollectionType,
        query_vector: list[float],
        top_k: int,
        score_threshold: float | None,
        filter_conditions: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        """Search single collection."""
        try:
            return await self._client.search_points(
                collection_name=collection.value,
                query_vector=query_vector,
                limit=top_k,
                score_threshold=score_threshold,
                filter_conditions=filter_conditions,
            )
        except Exception:
            return []

    async def search(self, request: SearchRequest) -> SearchResult:
        """Execute semantic search (async).

        Args:
            request: Search request parameters

        Returns:
            Search result with chunk references
        """
        start_time = time.time()

        query_vector = encode_text(request.query)
        top_k = min(request.top_k, MAX_TOP_K)

        filter_conditions = self._build_filter(request)
        collections = self._build_collections(request)

        tasks = [
            self._search_collection(
                collection=collection,
                query_vector=query_vector,
                top_k=top_k,
                score_threshold=request.min_score,
                filter_conditions=filter_conditions,
            )
            for collection in collections
        ]

        results_by_collection = await asyncio.gather(*tasks)

        all_chunks: list[ChunkReference] = []
        total_tokens = 0

        for collection_results in results_by_collection:
            for result in collection_results:
                payload = result.get("payload", {})
                content = payload.get("content", "")

                chunk_ref = ChunkReference(
                    chunk_id=str(result["id"]),
                    initiative_id=payload.get("initiative_id", ""),
                    chunk_type=payload.get("chunk_type", "unknown"),
                    summary=self._generate_summary(content),
                    relevance_score=result["score"],
                    payload=payload,
                )
                all_chunks.append(chunk_ref)
                total_tokens += payload.get("token_count", 0)

        all_chunks.sort(key=lambda x: x.relevance_score, reverse=True)
        top_chunks = all_chunks[:top_k]

        search_time = (time.time() - start_time) * 1000

        return SearchResult(
            chunks=top_chunks,
            total_retrieved=len(all_chunks),
            tokens_estimate=total_tokens,
            cached=False,
            search_time_ms=search_time,
        )

    def search_sync(self, request: SearchRequest) -> SearchResult:
        """Synchronous wrapper for search."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                raise RuntimeError("Cannot use sync search in async context")
            return asyncio.run(self.search(request))
        except RuntimeError:
            future = asyncio.ensure_future(self.search(request))
            return asyncio.run(future)

    def _generate_summary(self, content: str, max_chars: int = 100) -> str:
        """Generate short summary from content."""
        if not content:
            return ""
        content = content.strip()
        if len(content) <= max_chars:
            return content
        return content[: max_chars - 3] + "..."


_search_service: SemanticSearch | None = None


def get_search_service(
    client: QdrantVectorClient | None = None,
) -> SemanticSearch:
    """Get singleton search service."""
    global _search_service
    if _search_service is None:
        _search_service = SemanticSearch(client=client)
    return _search_service