"""Tests for EthosOS vector memory (Phase 4).

Requirements: MEM-01 through MEM-04
"""

import pytest


class TestChunking:
    """Test document chunking (Plan 4.2)."""

    def test_count_tokens(self):
        """Test token estimation."""
        from ethos_os.memory.chunker import count_tokens

        text = "one two three four five"
        tokens = count_tokens(text)
        assert tokens > 0
        assert tokens < 10

    def test_split_into_chunks(self):
        """Test text chunking with overlap."""
        from ethos_os.memory.chunker import split_into_chunks, count_tokens

        text = " ".join([f"word{i}" for i in range(2000)])
        chunks = split_into_chunks(text, chunk_size=512, overlap=50)

        assert len(chunks) > 1
        for chunk in chunks:
            assert count_tokens(chunk) <= 700

    def test_chunk_prd(self):
        """Test PRD chunking."""
        from ethos_os.memory.chunker import chunk_prd

        prd_data = {
            "intent": "Build a user authentication system",
            "success_metric": "99.9% uptime, <100ms login latency",
            "scope": "Login, logout, password reset, OAuth providers",
            "boundaries": "No social features, no admin panel",
        }

        chunks = chunk_prd(prd_data, "test-prd-id", "prd")

        assert len(chunks) == 4
        assert chunks[0].chunk_type.value == "intent"
        assert chunks[1].chunk_type.value == "success_metric"
        assert chunks[2].chunk_type.value == "scope"
        assert chunks[3].chunk_type.value == "boundaries"

        assert all(c.initiative_id == "test-prd-id" for c in chunks)
        assert all(c.total_chunks == 4 for c in chunks)

    def test_chunk_prd_minimal(self):
        """Test PRD with only required fields."""
        from ethos_os.memory.chunker import chunk_prd

        prd_data = {
            "intent": "Simple goal",
            "success_metric": "Measured outcome",
        }

        chunks = chunk_prd(prd_data, "minimal-prd", "prd")
        assert len(chunks) == 2

    def test_chunk_prd_empty(self):
        """Test PRD with no fields."""
        from ethos_os.memory.chunker import chunk_prd

        chunks = chunk_prd({}, "empty-prd", "prd")
        assert len(chunks) == 0

    def test_chunk_document(self):
        """Test generic document chunking."""
        from ethos_os.memory.chunker import chunk_document, ChunkType

        content = " ".join([f"section{i} content" for i in range(50)])
        chunks = chunk_document(
            content=content,
            document_id="doc-123",
            document_type=ChunkType.ARCHITECTURE,
            initiative_id="project-456",
            initiative_type="project",
        )

        assert len(chunks) >= 1
        assert all(c.initiative_id == "project-456" for c in chunks)

    def test_chunk_meeting_notes(self):
        """Test meeting notes chunking."""
        from ethos_os.memory.chunker import chunk_meeting_notes

        notes = """
        Meeting: Sprint Planning
        Attendees: Team A, Team B

        Discussion:
        - Feature prioritization
        - Technical debt

        Decisions:
        - Decided to prioritize auth first
        - Agreed on 2-week sprint

        Action Items:
        - [ ] Implement login
        - [ ] Setup database
        """

        chunks = chunk_meeting_notes(notes, "project-789", "project")
        assert len(chunks) >= 1
        assert all(c.chunk_type.value == "meeting_notes" for c in chunks)


class TestChunkReference:
    """Test chunk reference (token-efficient)."""

    def test_chunk_to_payload(self):
        """Test chunk serialization."""
        from ethos_os.memory.chunker import chunk_prd

        prd_data = {"intent": "Test intent", "success_metric": "Test metric"}
        chunks = chunk_prd(prd_data, "test-id", "prd")

        payload = chunks[0].to_payload()
        assert payload["chunk_id"] == chunks[0].chunk_id
        assert payload["initiative_id"] == "test-id"
        assert payload["content"] == chunks[0].content

    def test_chunk_get_summary(self):
        """Test summary generation."""
        from ethos_os.memory.chunker import chunk_prd

        prd_data = {"intent": "A" * 200}
        chunks = chunk_prd(prd_data, "test-id", "prd")

        summary = chunks[0].get_summary(max_chars=50)
        assert len(summary) <= 53
        assert summary.endswith("...")


class TestEmbeddings:
    """Test embedding generation."""

    def test_embedding_generator_init(self):
        """Test embedding generator initialization."""
        pytest.importorskip("sentence_transformers", reason="sentence-transformers required for embeddings")
        from ethos_os.memory.embeddings import EmbeddingGenerator, VECTOR_SIZE

        generator = EmbeddingGenerator()
        assert generator.dimension == VECTOR_SIZE

    def test_encode_single_text(self):
        """Test single text encoding."""
        pytest.importorskip("sentence_transformers", reason="sentence-transformers required for embeddings")
        from ethos_os.memory.embeddings import encode_text, VECTOR_SIZE

        vector = encode_text("Test document content")
        assert len(vector) == VECTOR_SIZE
        assert all(isinstance(x, float) for x in vector)

    def test_encode_batch(self):
        """Test batch encoding."""
        pytest.importorskip("sentence_transformers", reason="sentence-transformers required for embeddings")
        from ethos_os.memory.embeddings import encode_batch, VECTOR_SIZE

        texts = ["First document", "Second document", "Third document"]
        vectors = encode_batch(texts)

        assert len(vectors) == 3
        assert all(len(v) == VECTOR_SIZE for v in vectors)


class TestQdrantClient:
    """Test Qdrant client (Plan 4.1)."""

    def test_collection_types(self):
        """Test collection type enum."""
        from ethos_os.memory.collections import CollectionType

        assert CollectionType.PRD.value == "initiatives_prd"
        assert CollectionType.DOCS.value == "initiatives_docs"
        assert CollectionType.CONVERSATIONS.value == "initiatives_conversations"

    def test_qdrant_client_init(self):
        """Test Qdrant client initialization."""
        from ethos_os.memory.qdrant_client import QdrantVectorClient

        client = QdrantVectorClient(url="http://localhost:6333")
        assert client._url == "http://localhost:6333"
        assert client._vector_size == 384


class TestSearchService:
    """Test semantic search service (Plan 4.3)."""

    def test_search_request_defaults(self):
        """Test search request defaults."""
        from ethos_os.memory.search import SearchRequest, DEFAULT_TOP_K, DEFAULT_MIN_SCORE

        request = SearchRequest(query="test query")
        assert request.top_k == DEFAULT_TOP_K
        assert request.min_score == DEFAULT_MIN_SCORE
        assert request.initiative_id is None

    def test_chunk_reference_format(self):
        """Test chunk reference formatting."""
        from ethos_os.memory.search import ChunkReference

        ref = ChunkReference(
            chunk_id="test-123",
            initiative_id="init-456",
            chunk_type="intent",
            summary="Test summary",
            relevance_score=0.95,
        )

        formatted = ref.format_reference()
        assert "intent" in formatted
        assert "Test summary" in formatted
        assert "0.95" in formatted

    def test_search_result_format(self):
        """Test search result formatting."""
        from ethos_os.memory.search import ChunkReference, SearchResult

        chunks = [
            ChunkReference(
                chunk_id="1",
                initiative_id="init",
                chunk_type="intent",
                summary="First result",
                relevance_score=0.9,
            ),
            ChunkReference(
                chunk_id="2",
                initiative_id="init",
                chunk_type="scope",
                summary="Second result",
                relevance_score=0.8,
            ),
        ]

        result = SearchResult(
            chunks=chunks,
            total_retrieved=2,
            tokens_estimate=500,
            cached=False,
        )

        formatted = result.format_references()
        assert "Context from knowledge base" in formatted
        assert "1. [intent]" in formatted
        assert "2. [scope]" in formatted


class TestContextInjector:
    """Test context injection pipeline (Plan 4.3)."""

    def test_injector_init(self):
        """Test injector initialization."""
        from ethos_os.memory.injector import ContextInjector, DEFAULT_WORKING_MEMORY_TTL

        injector = ContextInjector()
        assert injector._working_memory_ttl == DEFAULT_WORKING_MEMORY_TTL

    def test_cache_key_generation(self):
        """Test cache key generation."""
        from ethos_os.memory.injector import ContextInjector

        injector = ContextInjector()

        key1 = injector._get_cache_key("agent-123", "initiative-456")
        key2 = injector._get_cache_key("agent-123", None)
        key3 = injector._get_cache_key("agent-789", "initiative-456")

        assert key1 != key2
        assert key1 != key3
        assert "agent-123" in key1
        assert "initiative-456" in key1


class TestInitiativeLinker:
    """Test initiative-memory linkage (Plan 4.4)."""

    def test_initiative_type_enum(self):
        """Test initiative type enum."""
        from ethos_os.memory.initiative_linker import InitiativeType

        assert InitiativeType.PORTFOLIO.value == "portfolio"
        assert InitiativeType.PROGRAM.value == "program"
        assert InitiativeType.PROJECT.value == "project"
        assert InitiativeType.PRD.value == "prd"

    def test_linker_init(self):
        """Test linker initialization."""
        from ethos_os.memory.initiative_linker import InitiativeLinker

        linker = InitiativeLinker()
        assert linker._indexer is not None
        assert linker._injector is not None


class TestWorkingMemoryIntegration:
    """Test working memory cache integration."""

    def test_working_memory_cache_operations(self):
        """Test cache get/set operations."""
        from ethos_os.memory.working import get_working_memory

        memory = get_working_memory()
        agent_id = memory.register()

        memory.cache_set("test", "key1", {"data": "value"}, ttl_seconds=60)
        value = memory.cache_get("test", "key1")

        assert value == {"data": "value"}

        memory.cache_delete("test", "key1")
        assert memory.cache_get("test", "key1") is None

    def test_working_memory_cache_expiry(self):
        """Test cache TTL expiration."""
        from datetime import datetime, timedelta
        from ethos_os.memory.working import get_working_memory, CacheEntry

        memory = get_working_memory()

        past = datetime.utcnow() - timedelta(seconds=10)
        memory._cache["test:expired"] = CacheEntry(
            value="old",
            expires_at=past,
        )

        assert memory.cache_get("test", "expired") is None


class TestMemoryPackageExports:
    """Test memory package exports."""

    def test_all_exports(self):
        """Test all expected exports are available."""
        from ethos_os.memory import (
            WorkingMemory,
            AgentContext,
            get_working_memory,
            QdrantVectorClient,
            get_qdrant_client,
            CollectionType,
            Chunk,
            ChunkType,
            chunk_prd,
            EmbeddingGenerator,
            encode_text,
            encode_batch,
            IndexingResult,
            MemoryIndexer,
            get_indexer,
            SearchRequest,
            SearchResult,
            SemanticSearch,
            get_search_service,
            ContextInjector,
            get_context_injector,
            InitiativeLinker,
            InitiativeType,
            get_initiative_linker,
        )

        assert WorkingMemory is not None
        assert get_working_memory() is not None
        assert get_qdrant_client() is not None
        assert get_indexer() is not None
        assert get_search_service() is not None
        assert get_context_injector() is not None
        assert get_initiative_linker() is not None


class TestTokenEfficiency:
    """Test token efficiency requirements."""

    def test_chunk_size_respected(self):
        """Test that chunk size is respected."""
        from ethos_os.memory.chunker import split_into_chunks, count_tokens

        long_text = " ".join([f"word{i}" for i in range(2000)])
        chunks = split_into_chunks(long_text, chunk_size=512, overlap=50)

        for chunk in chunks:
            tokens = count_tokens(chunk)
            assert tokens <= 700

    def test_top_k_limit(self):
        """Test that top-k limits results."""
        from ethos_os.memory.search import MAX_TOP_K

        assert MAX_TOP_K == 10

    def test_chunk_reference_small(self):
        """Test that chunk reference contains summary, not full content."""
        from ethos_os.memory.search import ChunkReference

        ref = ChunkReference(
            chunk_id="test",
            initiative_id="init",
            chunk_type="scope",
            summary="Short summary only",
            relevance_score=0.9,
        )

        formatted = ref.format_reference()
        assert len(formatted) < 500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])