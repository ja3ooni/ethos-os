"""Indexing pipeline for EthosOS vector memory.

Ties together chunking, embedding, and Qdrant storage.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ethos_os.memory.chunker import Chunk, ChunkType, chunk_meeting_notes, chunk_prd
from ethos_os.memory.collections import CollectionType
from ethos_os.memory.embeddings import encode_batch
from ethos_os.memory.qdrant_client import QdrantVectorClient, get_qdrant_client


@dataclass
class IndexingResult:
    """Result of indexing operation."""

    collection: str
    chunks_indexed: int
    tokens_indexed: int
    point_ids: list[str]


class MemoryIndexer:
    """Index documents to Qdrant vector store."""

    def __init__(self, client: QdrantVectorClient | None = None):
        """Initialize indexer.

        Args:
            client: Optional Qdrant client (creates singleton if not provided)
        """
        self._client = client or get_qdrant_client()

    async def index_prd(
        self,
        prd_id: str,
        prd_data: dict[str, Any],
        initiative_type: str = "prd",
    ) -> IndexingResult:
        """Index PRD document.

        Args:
            prd_id: PRD/Project ID
            prd_data: PRD fields (intent, success_metric, scope, boundaries)
            initiative_type: Parent initiative type

        Returns:
            Indexing result
        """
        chunks = chunk_prd(prd_data, prd_id, initiative_type)
        return await self._index_chunks(chunks, CollectionType.PRD)

    async def index_meeting_notes(
        self,
        meeting_id: str,
        notes: str,
        initiative_id: str,
        initiative_type: str = "project",
    ) -> IndexingResult:
        """Index meeting notes.

        Args:
            meeting_id: Meeting ID
            notes: Meeting notes text
            initiative_id: Parent initiative ID
            initiative_type: Initiative type

        Returns:
            Indexing result
        """
        chunks = chunk_meeting_notes(notes, initiative_id, initiative_type)
        if not chunks:
            return IndexingResult(
                collection=CollectionType.DOCS.value,
                chunks_indexed=0,
                tokens_indexed=0,
                point_ids=[],
            )

        for chunk in chunks:
            chunk.chunk_id = f"{meeting_id}_{chunk.chunk_id}"

        return await self._index_chunks(chunks, CollectionType.DOCS)

    async def index_document(
        self,
        document_id: str,
        content: str,
        document_type: ChunkType,
        initiative_id: str,
        initiative_type: str = "project",
    ) -> IndexingResult:
        """Index generic document.

        Args:
            document_id: Document ID
            content: Document content
            document_type: Type of document
            initiative_id: Parent initiative ID
            initiative_type: Initiative type

        Returns:
            Indexing result
        """
        from ethos_os.memory.chunker import chunk_document

        chunks = chunk_document(content, document_id, document_type, initiative_id, initiative_type)
        return await self._index_chunks(chunks, CollectionType.DOCS)

    async def _index_chunks(
        self,
        chunks: list[Chunk],
        collection_type: CollectionType,
    ) -> IndexingResult:
        """Index chunks to Qdrant.

        Args:
            chunks: List of chunks
            collection_type: Target collection

        Returns:
            Indexing result
        """
        if not chunks:
            return IndexingResult(
                collection=collection_type.value,
                chunks_indexed=0,
                tokens_indexed=0,
                point_ids=[],
            )

        collection_name = collection_type.value

        await self._client.create_collection(collection_type)

        contents = [chunk.content for chunk in chunks]
        vectors = encode_batch(contents)

        points = []
        point_ids = []
        total_tokens = 0

        for chunk, vector in zip(chunks, vectors):
            payload = chunk.to_payload()
            payload["content"] = chunk.content

            points.append({
                "id": chunk.chunk_id,
                "vector": vector,
                "payload": payload,
            })
            point_ids.append(chunk.chunk_id)
            total_tokens += chunk.token_count

        await self._client.upsert_points(collection_name, points)

        return IndexingResult(
            collection=collection_name,
            chunks_indexed=len(chunks),
            tokens_indexed=total_tokens,
            point_ids=point_ids,
        )

    async def delete_initiative_chunks(
        self,
        initiative_id: str,
        collection_type: CollectionType | None = None,
    ) -> int:
        """Delete all chunks for an initiative.

        Args:
            initiative_id: Initiative ID to delete
            collection_type: Specific collection (or all if None)

        Returns:
            Number of chunks deleted
        """
        filter_conditions = {
            "must": [
                {
                    "key": "initiative_id",
                    "match": {"value": initiative_id},
                }
            ]
        }

        deleted = 0

        collections = [collection_type] if collection_type else CollectionType

        for col in collections:
            result = await self._client.delete_by_filter(
                col.value,
                filter_conditions,
            )
            deleted += result

        return deleted

    async def reindex_prd(
        self,
        prd_id: str,
        prd_data: dict[str, Any],
        initiative_type: str = "prd",
    ) -> IndexingResult:
        """Reindex PRD (delete old, index new).

        Args:
            prd_id: PRD/Project ID
            prd_data: Updated PRD fields
            initiative_type: Parent initiative type

        Returns:
            Indexing result
        """
        await self.delete_initiative_chunks(prd_id, CollectionType.PRD)
        return await self.index_prd(prd_id, prd_data, initiative_type)


_indexer: MemoryIndexer | None = None


def get_indexer() -> MemoryIndexer:
    """Get singleton memory indexer."""
    global _indexer
    if _indexer is None:
        _indexer = MemoryIndexer()
    return _indexer