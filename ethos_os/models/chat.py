"""Chat models for EthosOS v0.2.

Chat-01: Paperclip-style chat interface with conversation history
Chat-02: Initiative context injection - selected initiative passed to agent
Chat-03: Agent switching - talk to different agents mid-conversation
Chat-04: Real-time updates via SSE/WebSocket
Chat-05: SQLite persistence for conversation history
Chat-06: Chat → Initiative linking - conversations trace to initiative
"""

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ethos_os.db import Base


class Conversation(Base):
    """Chat conversation - linked to initiative context."""

    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    user_id: Mapped[str] = mapped_column(
        String(36),
        nullable=True,
        doc="User who owns this conversation"
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="New Conversation",
        doc="Conversation title"
    )

    # Initiative linkage - Chat → Initiative linking
    initiative_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        doc="Link to Program/Project/Sprint (PRD gate must pass)"
    )

    initiative_type: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        doc="program, project, sprint, or task"
    )

    # Agent context - current agent being talked to
    current_agent_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        doc="Current agent in this conversation"
    )

    current_agent_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Display name for current agent"
    )

    # Token-efficient: summary of conversation (not full history)
    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Auto-generated summary (for token efficiency)"
    )

    # Message counts for display
    message_count: Mapped[int] = mapped_column(
        default=0,
        doc="Total messages in conversation"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        doc="Conversation is active"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    __table_args__ = (
        Index("ix_conversations_user", "user_id"),
        Index("ix_conversations_initiative", "initiative_id"),
        Index("ix_conversations_active", "is_active"),
        Index("ix_conversations_updated", "updated_at"),
    )


class Message(Base):
    """Individual chat message."""

    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    conversation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conversations.id"),
        nullable=False,
    )

    # Message role
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="user, assistant, system"
    )

    # Content
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Message content"
    )

    # Token tracking
    token_count: Mapped[int | None] = mapped_column(
        nullable=True,
        doc="Token count for this message"
    )

    # Agent reference (for assistant messages)
    agent_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        doc="Agent that generated this response"
    )

    agent_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Agent display name"
    )

    message_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        doc="Additional message metadata"
    )

    # Token-efficient: is this message summarized?
    is_summarized: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        doc="Message was summarized to save tokens"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )

    __table_args__ = (
        Index("ix_messages_conversation", "conversation_id"),
        Index("ix_messages_created", "created_at"),
    )


class InitiativeContext(Base):
    """Cached initiative context for chat injection.
    
    Chat-02: Initiative context injection - passed to agent
    Stored in working memory cache, invalidated on initiative updates.
    """

    __tablename__ = "initiative_contexts"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    initiative_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        doc="Program/Project/Sprint ID"
    )

    initiative_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="program, project, sprint, task"
    )

    # Token-efficient context chunks
    context_chunks: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        doc="Qdrant-retrieved context chunks"
    )

    # Summary for display
    summary: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        doc="Context summary for UI"
    )

    # TTL tracking
    cached_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="Cache expiration time"
    )

    __table_args__ = (
        Index("ix_initiative_contexts_initiative", "initiative_id", unique=True),
    )