"""Document chunking for EthosOS vector memory.

Token-efficient chunking at 512 tokens with overlap for context continuity.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class ChunkType(str, Enum):
    """Types of content chunks."""

    INTENT = "intent"
    SUCCESS_METRIC = "success_metric"
    SCOPE = "scope"
    BOUNDARIES = "boundaries"
    MEETING_NOTES = "meeting_notes"
    ARCHITECTURE = "architecture"
    CONVERSATION = "conversation"


@dataclass
class Chunk:
    """A document chunk for vector storage."""

    chunk_id: str
    content: str
    chunk_type: ChunkType
    initiative_id: str
    initiative_type: str
    token_count: int
    chunk_index: int
    total_chunks: int
    metadata: dict[str, Any] | None = None

    def to_payload(self) -> dict[str, Any]:
        """Convert to Qdrant payload."""
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "chunk_type": self.chunk_type.value,
            "initiative_id": self.initiative_id,
            "initiative_type": self.initiative_type,
            "token_count": self.token_count,
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "metadata": self.metadata or {},
        }

    def get_summary(self, max_chars: int = 100) -> str:
        """Get short summary for reference injection."""
        text = self.content.strip()
        if len(text) <= max_chars:
            return text
        return text[: max_chars - 3] + "..."


DEFAULT_CHUNK_SIZE = 512
DEFAULT_OVERLAP = 50
MAX_CHUNKS_PER_DOCUMENT = 20


def count_tokens(text: str) -> int:
    """Estimate token count (rough approximation).

    Uses word-based estimation: ~0.75 tokens per word for English.
    More accurate would use tiktoken or similar.
    """
    words = text.split()
    return int(len(words) / 0.75)


def split_into_chunks(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
    max_chunks: int = MAX_CHUNKS_PER_DOCUMENT,
) -> list[str]:
    """Split text into token-sized chunks with overlap.

    Args:
        text: Text to chunk
        chunk_size: Target tokens per chunk
        overlap: Token overlap between chunks
        max_chunks: Maximum chunks per document

    Returns:
        List of text chunks
    """
    if not text.strip():
        return []

    words = text.split()
    if len(words) < chunk_size:
        return [text]

    chunks = []
    step = chunk_size - overlap
    start = 0

    while start < len(words):
        chunk_words = words[start : start + chunk_size]
        chunks.append(" ".join(chunk_words))

        if len(chunks) >= max_chunks:
            break

        start += step

    return chunks


def chunk_prd(prd_data: dict[str, Any], initiative_id: str, initiative_type: str = "prd") -> list[Chunk]:
    """Chunk a PRD document.

    PRD Structure:
    - intent: single chunk (~100 tokens)
    - success_metric: single chunk (~150 tokens)
    - scope: chunked at 512 tokens
    - boundaries: single chunk (~100 tokens)

    Args:
        prd_data: PRD fields (intent, success_metric, scope, boundaries)
        initiative_id: PRD/Project ID
        initiative_type: Initiative type (prd, project)

    Returns:
        List of chunks
    """
    chunks = []
    chunk_index = 0

    intent = prd_data.get("intent", "")
    if intent:
        chunks.append(
            Chunk(
                chunk_id=f"{initiative_id}_{ChunkType.INTENT.value}_{chunk_index}",
                content=intent,
                chunk_type=ChunkType.INTENT,
                initiative_id=initiative_id,
                initiative_type=initiative_type,
                token_count=count_tokens(intent),
                chunk_index=chunk_index,
                total_chunks=0,
            )
        )
        chunk_index += 1

    success_metric = prd_data.get("success_metric", "")
    if success_metric:
        chunks.append(
            Chunk(
                chunk_id=f"{initiative_id}_{ChunkType.SUCCESS_METRIC.value}_{chunk_index}",
                content=success_metric,
                chunk_type=ChunkType.SUCCESS_METRIC,
                initiative_id=initiative_id,
                initiative_type=initiative_type,
                token_count=count_tokens(success_metric),
                chunk_index=chunk_index,
                total_chunks=0,
            )
        )
        chunk_index += 1

    scope = prd_data.get("scope", "")
    if scope:
        scope_chunks = split_into_chunks(scope)
        for i, content in enumerate(scope_chunks):
            chunks.append(
                Chunk(
                    chunk_id=f"{initiative_id}_{ChunkType.SCOPE.value}_{chunk_index}",
                    content=content,
                    chunk_type=ChunkType.SCOPE,
                    initiative_id=initiative_id,
                    initiative_type=initiative_type,
                    token_count=count_tokens(content),
                    chunk_index=chunk_index,
                    total_chunks=0,
                )
            )
            chunk_index += 1

    boundaries = prd_data.get("boundaries", "")
    if boundaries:
        chunks.append(
            Chunk(
                chunk_id=f"{initiative_id}_{ChunkType.BOUNDARIES.value}_{chunk_index}",
                content=boundaries,
                chunk_type=ChunkType.BOUNDARIES,
                initiative_id=initiative_id,
                initiative_type=initiative_type,
                token_count=count_tokens(boundaries),
                chunk_index=chunk_index,
                total_chunks=0,
            )
        )
        chunk_index += 1

    total = len(chunks)
    for i in range(total):
        chunks[i].total_chunks = total

    return chunks


def chunk_document(
    content: str,
    document_id: str,
    document_type: ChunkType,
    initiative_id: str,
    initiative_type: str = "project",
) -> list[Chunk]:
    """Chunk a generic document.

    Args:
        content: Document content
        document_id: Document ID
        document_type: Type of document
        initiative_id: Parent initiative ID
        initiative_type: Initiative type

    Returns:
        List of chunks
    """
    if not content.strip():
        return []

    text_chunks = split_into_chunks(content)
    chunks = []

    for i, text in enumerate(text_chunks):
        chunks.append(
            Chunk(
                chunk_id=f"{document_id}_{document_type.value}_{i}",
                content=text,
                chunk_type=document_type,
                initiative_id=initiative_id,
                initiative_type=initiative_type,
                token_count=count_tokens(text),
                chunk_index=i,
                total_chunks=len(text_chunks),
            )
        )

    return chunks


def chunk_meeting_notes(
    notes: str,
    initiative_id: str,
    initiative_type: str = "project",
) -> list[Chunk]:
    """Chunk meeting notes, extracting key decisions.

    Args:
        notes: Meeting notes text
        initiative_id: Parent initiative ID
        initiative_type: Initiative type

    Returns:
        List of chunks with key decisions highlighted
    """
    if not notes.strip():
        return []

    lines = notes.split("\n")
    key_decisions = []
    current_decision = []
    in_decisions = False

    decision_pattern = re.compile(r"(decided|agreed|resolved|actioned|to-do|next steps?):", re.IGNORECASE)
    decision_indicators = ["- [x]", "- [ ]", "**Decision:**", "**Action:**", "**TODO:**"]

    for line in lines:
        if decision_pattern.search(line):
            in_decisions = True
            if current_decision:
                key_decisions.append("\n".join(current_decision))
            current_decision = [line]
        elif in_decisions:
            if line.strip().startswith("- ") or line.strip().startswith("* ") or line.strip() == "":
                current_decision.append(line)
            else:
                key_decisions.append("\n".join(current_decision))
                current_decision = []
                in_decisions = False
        elif any(indicator in line for indicator in decision_indicators):
            key_decisions.append(line)

    if current_decision:
        key_decisions.append("\n".join(current_decision))

    if key_decisions:
        content = "\n\n".join(key_decisions)
    else:
        content = notes

    return chunk_document(content, f"meeting_{initiative_id}", ChunkType.MEETING_NOTES, initiative_id, initiative_type)