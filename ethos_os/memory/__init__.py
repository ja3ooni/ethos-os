"""Memory package for EthosOS vector memory.

Modules:
- working: Per-agent working memory with TTL cache
- qdrant_client: Async Qdrant client wrapper
- chunker: Document chunking at 512 tokens
- embeddings: Sentence-transformers embedding generation
- indexer: Indexing pipeline (chunk → embed → upload)
- search: Semantic search with top-k retrieval
- injector: Context injection pipeline for agents
- initiative_linker: Initiative-memory linkage and cache invalidation
"""

# Working memory (existing)
from ethos_os.memory.working import AgentContext, WorkingMemory, get_working_memory

# Qdrant client
from ethos_os.memory.qdrant_client import (
    QdrantVectorClient,
    get_qdrant_client,
)

# Collections
from ethos_os.memory.collections import CollectionType as CollectionType
from ethos_os.memory.chunker import (
    Chunk,
    ChunkType,
    chunk_meeting_notes,
    chunk_prd,
    split_into_chunks,
    count_tokens,
)

# Embeddings
from ethos_os.memory.embeddings import (
    EmbeddingGenerator,
    encode_batch,
    encode_text,
    get_embedding_generator,
)

# Indexer
from ethos_os.memory.indexer import (
    IndexingResult,
    MemoryIndexer,
    get_indexer,
)

# Search
from ethos_os.memory.search import (
    ChunkReference,
    SearchRequest,
    SearchResult,
    SemanticSearch,
    get_search_service,
)

# Context injection
from ethos_os.memory.injector import (
    AgentContextResponse,
    ContextInjector,
    InjectedContext,
    get_context_injector,
)

# Initiative linker
from ethos_os.memory.initiative_linker import (
    InitiativeLinker,
    InitiativeType,
    LinkageEvent,
    get_initiative_linker,
)

__all__ = [
    # Working memory
    "WorkingMemory",
    "AgentContext",
    "get_working_memory",
    # Qdrant client
    "QdrantVectorClient",
    "get_qdrant_client",
    # Collections
    "CollectionType",
    # Chunker
    "Chunk",
    "ChunkType",
    "chunk_prd",
    "chunk_meeting_notes",
    "split_into_chunks",
    "count_tokens",
    # Embeddings
    "EmbeddingGenerator",
    "encode_text",
    "encode_batch",
    "get_embedding_generator",
    # Indexer
    "IndexingResult",
    "MemoryIndexer",
    "get_indexer",
    # Search
    "SearchRequest",
    "SearchResult",
    "ChunkReference",
    "SemanticSearch",
    "get_search_service",
    # Context injection
    "ContextInjector",
    "AgentContextResponse",
    "InjectedContext",
    "get_context_injector",
    # Initiative linker
    "InitiativeLinker",
    "InitiativeType",
    "LinkageEvent",
    "get_initiative_linker",
]