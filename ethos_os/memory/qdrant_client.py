"""Qdrant vector database client for EthosOS.

Provides async Qdrant client with collections for initiative content.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams


class CollectionType(str, Enum):
    """Collection types for initiative content."""

    PRD = "initiatives_prd"
    DOCS = "initiatives_docs"
    CONVERSATIONS = "initiatives_conversations"


@dataclass
class CollectionConfig:
    """Collection configuration."""

    name: str
    vector_size: int = 384
    distance: Distance = Distance.COSINE
    description: str = ""


COLLECTION_CONFIGS: dict[CollectionType, CollectionConfig] = {
    CollectionType.PRD: CollectionConfig(
        name=CollectionType.PRD.value,
        vector_size=384,
        description="PRD chunks: intent, success_metric, scope, boundaries",
    ),
    CollectionType.DOCS: CollectionConfig(
        name=CollectionType.DOCS.value,
        vector_size=384,
        description="Architecture docs and meeting notes",
    ),
    CollectionType.CONVERSATIONS: CollectionConfig(
        name=CollectionType.CONVERSATIONS.value,
        vector_size=384,
        description="Chat message embeddings",
    ),
}


class QdrantVectorClient:
    """Async Qdrant client for EthosOS vector operations."""

    def __init__(
        self,
        url: str = "http://localhost:6333",
        api_key: str | None = None,
        vector_size: int = 384,
    ):
        """Initialize Qdrant client.

        Args:
            url: Qdrant server URL
            api_key: Optional API key
            vector_size: Embedding vector size
        """
        self._url = url
        self._api_key = api_key
        self._vector_size = vector_size
        self._client: AsyncQdrantClient | None = None
        self._lock = asyncio.Lock()

    async def _get_client(self) -> AsyncQdrantClient:
        """Get or create async client."""
        if self._client is None:
            async with self._lock:
                if self._client is None:
                    self._client = AsyncQdrantClient(
                        url=self._url,
                        api_key=self._api_key,
                    )
        return self._client

    async def close(self) -> None:
        """Close client connection."""
        if self._client:
            async with self._lock:
                if self._client:
                    await self._client.close()
                    self._client = None

    async def health_check(self) -> bool:
        """Check Qdrant health."""
        client = await self._get_client()
        try:
            info = await client.info()
            return info is not None
        except Exception:
            return False

    async def collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists."""
        client = await self._get_client()
        try:
            await client.get_collection(collection_name)
            return True
        except Exception:
            return False

    async def create_collection(self, collection_type: CollectionType) -> bool:
        """Create collection if not exists.

        Args:
            collection_type: Type of collection to create

        Returns:
            True if created, False if already exists
        """
        config = COLLECTION_CONFIGS.get(collection_type)
        if not config:
            raise ValueError(f"Unknown collection type: {collection_type}")

        if await self.collection_exists(config.name):
            return False

        client = await self._get_client()
        from qdrant_client.models import OptimizersConfig

        await client.create_collection(
            collection_name=config.name,
            vectors_config=VectorParams(
                size=config.vector_size,
                distance=config.distance,
            ),
            optimizers_config=OptimizersConfig(
                indexed_vectors=1024,
                quantized_vectors=2048,
            ),
            description=config.description,
        )
        return True

    async def create_all_collections(self) -> list[str]:
        """Create all initiative collections.

        Returns:
            List of created collection names
        """
        created = []
        for collection_type in CollectionType:
            if await self.create_collection(collection_type):
                created.append(COLLECTION_CONFIGS[collection_type].name)
        return created

    async def delete_collection(self, collection_name: str) -> bool:
        """Delete collection.

        Args:
            collection_name: Collection to delete

        Returns:
            True if deleted
        """
        client = await self._get_client()
        try:
            await client.delete_collection(collection_name)
            return True
        except Exception:
            return False

    async def get_collection_info(self, collection_name: str) -> dict[str, Any] | None:
        """Get collection info."""
        client = await self._get_client()
        try:
            info = await client.get_collection(collection_name)
            return {
                "name": info.name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
            }
        except Exception:
            return None

    async def upsert_points(
        self,
        collection_name: str,
        points: list[dict[str, Any]],
    ) -> str:
        """Upsert points to collection.

        Args:
            collection_name: Target collection
            points: List of point dicts with id, vector, payload

        Returns:
            Operation status
        """
        client = await self._get_client()

        from qdrant_client.models import PointStruct

        result = await client.upsert(
            collection_name=collection_name,
            points=[
                PointStruct(
                    id=point["id"],
                    vector=point["vector"],
                    payload=point.get("payload", {}),
                )
                for point in points
            ],
        )
        return result.result.status if result.result else "unknown"

    async def search_points(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 5,
        score_threshold: float | None = 0.7,
        filter_conditions: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search points by vector.

        Args:
            collection_name: Collection to search
            query_vector: Query embedding vector
            limit: Max results to return
            score_threshold: Minimum similarity score
            filter_conditions: Optional filters

        Returns:
            List of matching points with scores
        """
        from qdrant_client.models import Filter, MatchValue

        client = await self._get_client()

        query_filter = None
        if filter_conditions:
            must = []
            for cond in filter_conditions.get("must", []):
                key = cond.get("key")
                match = cond.get("match", {})
                if key == "initiative_id":
                    must.append(
                        Filter(
                            key=key,
                            match=MatchValue(value=match.get("value")),
                        )
                    )
            if must:
                query_filter = Filter(must=must)

        results = await client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=query_filter,
        )

        return [
            {
                "id": str(r.id),
                "score": r.score,
                "payload": r.payload or {},
            }
            for r in results
        ]

    async def scroll_points(
        self,
        collection_name: str,
        offset: str | None = None,
        limit: int = 100,
        filter_conditions: dict[str, Any] | None = None,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Scroll through collection points.

        Args:
            collection_name: Collection to scroll
            offset: Pagination offset
            limit: Page size
            filter_conditions: Optional filters

        Returns:
            Tuple of (points, next_offset)
        """
        client = await self._get_client()

        results, next_offset = await client.scroll(
            collection_name=collection_name,
            offset=offset,
            limit=limit,
            with_payload=True,
        )

        points = [
            {
                "id": str(r.id),
                "vector": r.vector if hasattr(r, "vector") else None,
                "payload": r.payload or {},
            }
            for r in results
        ]

        return points, next_offset

    async def delete_points(
        self,
        collection_name: str,
        point_ids: list[str],
    ) -> int:
        """Delete points by ID.

        Args:
            collection_name: Collection
            point_ids: Point IDs to delete

        Returns:
            Number deleted
        """
        from qdrant_client.models import PointIdsList

        client = await self._get_client()

        await client.delete(
            collection_name=collection_name,
            points_selector=PointIdsList(points=point_ids),
        )
        return len(point_ids)

    async def delete_by_filter(
        self,
        collection_name: str,
        filter_conditions: dict[str, Any],
    ) -> int:
        """Delete points matching filter.

        Args:
            collection_name: Collection
            filter_conditions: Filter to match

        Returns:
            Number deleted (estimated)
        """
        from qdrant_client.models import Filter, FilterSelector, MatchValue

        client = await self._get_client()

        must = []
        for cond in filter_conditions.get("must", []):
            key = cond.get("key")
            match = cond.get("match", {})
            if key == "initiative_id":
                must.append(
                    Filter(
                        key=key,
                        match=MatchValue(value=match.get("value")),
                    )
                )

        if not must:
            return 0

        result = await client.delete(
            collection_name=collection_name,
            points_selector=FilterSelector(
                filter=Filter(must=must)
            ),
        )
        return result.deleted or 0

    async def count_points(self, collection_name: str) -> int:
        """Count points in collection."""
        client = await self._get_client()
        count = await client.count(collection_name)
        return count.count


_qdrant_client: QdrantVectorClient | None = None


def get_qdrant_client(
    url: str = "http://localhost:6333",
    api_key: str | None = None,
    vector_size: int = 384,
) -> QdrantVectorClient:
    """Get singleton Qdrant client."""
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantVectorClient(url=url, api_key=api_key, vector_size=vector_size)
    return _qdrant_client