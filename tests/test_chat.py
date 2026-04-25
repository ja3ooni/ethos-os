"""Tests for Chat UI Phase 3."""

import pytest
from uuid import uuid4

from ethos_os.models.chat import Conversation, Message
from ethos_os.repositories.chat import ChatRepository
from ethos_os.db import get_session


@pytest.fixture
def session():
    """Get database session."""
    with get_session() as sess:
        yield sess


@pytest.fixture
def chat_repo(session):
    """Get chat repository."""
    return ChatRepository(session)


class TestConversation:
    """Test conversation operations."""

    def test_create_conversation(self, chat_repo):
        """Test creating a conversation."""
        conv = chat_repo.get_or_create_conversation(
            initiative_id="test-init-123",
            title="Test Chat"
        )
        
        assert conv is not None
        assert conv.title == "Test Chat"
        assert conv.initiative_id == "test-init-123"
        assert conv.is_active is True

    def test_get_conversation_by_initiative(self, chat_repo):
        """Test getting conversation by initiative."""
        conv1 = chat_repo.get_or_create_conversation(
            initiative_id="init-456",
            title="Test 1"
        )
        conv2 = chat_repo.get_or_create_conversation(
            initiative_id="init-456",
            title="Test 2"
        )
        
        assert conv1.id == conv2.id

    def test_conversation_with_agent(self, chat_repo):
        """Test conversation with agent context."""
        conv = chat_repo.get_or_create_conversation(
            initiative_id="init-789",
            title="Agent Chat"
        )
        
        agent_id = str(uuid4())
        
        msg = chat_repo.add_message(
            conversation_id=conv.id,
            role="user",
            content="Hello agent"
        )
        
        assert msg is not None
        assert msg.role == "user"
        assert msg.content == "Hello agent"
        
        response = chat_repo.add_message(
            conversation_id=conv.id,
            role="assistant",
            content="Hello human",
            agent_id=agent_id,
            agent_name="Test Agent"
        )
        
        assert response.agent_id == agent_id
        assert response.agent_name == "Test Agent"


class TestMessageSummarization:
    """Test message summarization for token efficiency."""

    def test_summarize_old_messages(self, chat_repo):
        """Test conversation summarization."""
        conv = chat_repo.get_or_create_conversation(
            title="Summary Test"
        )
        
        for i in range(15):
            chat_repo.add_message(
                conversation_id=conv.id,
                role="user",
                content=f"Message {i}"
            )
        
        summary = chat_repo.summarize_conversation(conv.id)
        
        assert summary is not None
        assert len(summary) > 0

    def test_get_context_for_agent(self, chat_repo):
        """Test getting token-efficient context."""
        conv = chat_repo.get_or_create_conversation(
            initiative_id="ctx-init",
            title="Context Test"
        )
        
        chat_repo.add_message(
            conversation_id=conv.id,
            role="user",
            content="Test message"
        )
        
        context = chat_repo.get_context_for_agent(conv.id)
        
        assert context is not None
        assert context["initiative_id"] == "ctx-init"
        assert context["title"] == "Context Test"


class TestInitiativeContext:
    """Test initiative context caching."""

    def test_cache_initiative_context(self, chat_repo, session):
        """Test caching initiative context."""
        init_id = f"init-{uuid4()}"
        
        chunks = [
            {"topic": "Project overview", "content": "Building a new feature"},
            {"topic": "Sprint goal", "content": "Complete Phase 3"}
        ]
        
        ctx = chat_repo.cache_initiative_context(
            initiative_id=init_id,
            initiative_type="project",
            context_chunks=chunks,
            ttl_seconds=60
        )
        
        assert ctx is not None
        assert ctx.initiative_id == init_id
        assert len(ctx.context_chunks) == 2
        
        cached = chat_repo.get_initiative_context(init_id)
        assert cached is not None
        assert cached.initiative_id == init_id

    def test_context_expiration(self, chat_repo):
        """Test context expiration."""
        init_id = f"exp-{uuid4()}"
        
        chat_repo.cache_initiative_context(
            initiative_id=init_id,
            initiative_type="project",
            context_chunks=[{"content": "test"}],
            ttl_seconds=1
        )
        
        import time
        time.sleep(2)
        
        cached = chat_repo.get_initiative_context(init_id)
        assert cached is None

    def test_invalidate_context(self, chat_repo):
        """Test invalidating context."""
        init_id = f"inv-{uuid4()}"
        
        chat_repo.cache_initiative_context(
            initiative_id=init_id,
            initiative_type="project",
            context_chunks=[{"content": "test"}]
        )
        
        result = chat_repo.invalidate_initiative_context(init_id)
        assert result is True
        
        cached = chat_repo.get_initiative_context(init_id)
        assert cached is None


class TestChatAPI:
    """Test chat API endpoints - basic validation."""

    def test_conversation_model_basic(self, session):
        """Basic model test."""
        from ethos_os.models.chat import Conversation
        assert Conversation is not None

    def test_message_model_basic(self, session):
        """Basic model test."""
        from ethos_os.models.chat import Message
        assert Message is not None

    def test_initiative_context_model_basic(self, session):
        """Basic model test."""
        from ethos_os.models.chat import InitiativeContext
        assert InitiativeContext is not None