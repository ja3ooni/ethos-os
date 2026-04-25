"""Initiative-memory linkage for EthosOS vector memory.

Links vector chunks to initiative hierarchy with cache invalidation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from ethos_os.memory.chunker import ChunkType
from ethos_os.memory.indexer import MemoryIndexer, get_indexer
from ethos_os.memory.injector import ContextInjector, get_context_injector


class InitiativeType(str, Enum):
    """Initiative hierarchy types."""

    PORTFOLIO = "portfolio"
    PROGRAM = "program"
    PROJECT = "project"
    SPRINT = "sprint"
    TASK = "task"
    PRD = "prd"


@dataclass
class LinkageEvent:
    """Event for initiative-memory linkage changes."""

    event_type: str
    initiative_id: str
    initiative_type: InitiativeType
    timestamp: str
    details: dict[str, Any] | None = None


class InitiativeLinker:
    """Link vector memory to initiative hierarchy.

    Responsibilities:
    - Auto-index initiatives when created/updated
    - Delete chunks when initiatives deleted
    - Invalidate cache on updates
    """

    def __init__(
        self,
        indexer: MemoryIndexer | None = None,
        injector: ContextInjector | None = None,
    ):
        """Initialize initiative linker.

        Args:
            indexer: Optional memory indexer
            injector: Optional context injector
        """
        self._indexer = indexer or get_indexer()
        self._injector = injector or get_context_injector()

    async def on_prd_created(
        self,
        prd_id: str,
        prd_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Handle PRD creation - index PRD chunks.

        Args:
            prd_id: PRD ID
            prd_data: PRD fields (intent, success_metric, scope, boundaries)

        Returns:
            Indexing result details
        """
        result = await self._indexer.index_prd(
            prd_id=prd_id,
            prd_data=prd_data,
            initiative_type=InitiativeType.PRD.value,
        )

        return {
            "event": "prd_created",
            "prd_id": prd_id,
            "chunks_indexed": result.chunks_indexed,
            "tokens_indexed": result.tokens_indexed,
        }

    async def on_prd_updated(
        self,
        prd_id: str,
        prd_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Handle PRD update - reindex and invalidate cache.

        Args:
            prd_id: PRD ID
            prd_data: Updated PRD fields

        Returns:
            Reindexing result details
        """
        result = await self._indexer.reindex_prd(
            prd_id=prd_id,
            prd_data=prd_data,
            initiative_type=InitiativeType.PRD.value,
        )

        self._injector.invalidate_initiative(prd_id)

        return {
            "event": "prd_updated",
            "prd_id": prd_id,
            "chunks_reindexed": result.chunks_indexed,
            "cache_invalidated": True,
        }

    async def on_initiative_deleted(
        self,
        initiative_id: str,
        initiative_type: InitiativeType = InitiativeType.PROJECT,
    ) -> dict[str, Any]:
        """Handle initiative deletion - delete all related chunks.

        Args:
            initiative_id: Initiative ID
            initiative_type: Type of initiative

        Returns:
            Deletion result details
        """
        deleted = await self._indexer.delete_initiative_chunks(initiative_id)

        self._injector.invalidate_initiative(initiative_id)

        return {
            "event": "initiative_deleted",
            "initiative_id": initiative_id,
            "initiative_type": initiative_type.value,
            "chunks_deleted": deleted,
            "cache_invalidated": True,
        }

    async def on_meeting_notes_added(
        self,
        meeting_id: str,
        notes: str,
        initiative_id: str,
        initiative_type: InitiativeType = InitiativeType.PROJECT,
    ) -> dict[str, Any]:
        """Handle meeting notes added - index key decisions.

        Args:
            meeting_id: Meeting ID
            notes: Meeting notes text
            initiative_id: Parent initiative ID
            initiative_type: Initiative type

        Returns:
            Indexing result details
        """
        result = await self._indexer.index_meeting_notes(
            meeting_id=meeting_id,
            notes=notes,
            initiative_id=initiative_id,
            initiative_type=initiative_type.value,
        )

        self._injector.invalidate_initiative(initiative_id)

        return {
            "event": "meeting_notes_added",
            "meeting_id": meeting_id,
            "initiative_id": initiative_id,
            "chunks_indexed": result.chunks_indexed,
            "tokens_indexed": result.tokens_indexed,
        }

    async def on_document_indexed(
        self,
        document_id: str,
        content: str,
        document_type: ChunkType,
        initiative_id: str,
        initiative_type: InitiativeType = InitiativeType.PROJECT,
    ) -> dict[str, Any]:
        """Handle document indexed - index and invalidate cache.

        Args:
            document_id: Document ID
            content: Document content
            document_type: Type of document
            initiative_id: Parent initiative ID
            initiative_type: Initiative type

        Returns:
            Indexing result details
        """
        result = await self._indexer.index_document(
            document_id=document_id,
            content=content,
            document_type=document_type,
            initiative_id=initiative_id,
            initiative_type=initiative_type.value,
        )

        self._injector.invalidate_initiative(initiative_id)

        return {
            "event": "document_indexed",
            "document_id": document_id,
            "initiative_id": initiative_id,
            "chunks_indexed": result.chunks_indexed,
            "tokens_indexed": result.tokens_indexed,
        }

    def invalidate_cache(self, initiative_id: str) -> int:
        """Manually invalidate cache for an initiative.

        Args:
            initiative_id: Initiative ID

        Returns:
            Number of cache entries invalidated
        """
        return self._injector.invalidate_initiative(initiative_id)


_linker: InitiativeLinker | None = None


def get_initiative_linker() -> InitiativeLinker:
    """Get singleton initiative linker."""
    global _linker
    if _linker is None:
        _linker = InitiativeLinker()
    return _linker