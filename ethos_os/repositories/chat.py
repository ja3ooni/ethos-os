"""Chat repository with token-efficient operations.

CHAT-05: Message persistence with summarization
"""

from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from ethos_os.db import get_session
from ethos_os.models.chat import Conversation, Message, InitiativeContext


class ChatRepository:
    """Token-efficient chat operations."""

    def __init__(self, session: Session):
        self.session = session

    def get_or_create_conversation(
        self,
        initiative_id: str | None = None,
        user_id: str | None = None,
        title: str | None = None,
    ) -> Conversation:
        """Get or create conversation linked to initiative."""
        query = self.session.query(Conversation)
        
        if initiative_id:
            query = query.filter(Conversation.initiative_id == initiative_id)
        if user_id:
            query = query.filter(Conversation.user_id == user_id)
        
        conv = query.filter(Conversation.is_active == True).first()
        
        if not conv:
            conv = Conversation(
                id=str(uuid4()),
                user_id=user_id,
                title=title or "New Conversation",
                initiative_id=initiative_id,
            )
            self.session.add(conv)
            self.session.flush()
        
        return conv

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        agent_id: str | None = None,
        agent_name: str | None = None,
    ) -> Message:
        """Add message to conversation."""
        msg = Message(
            id=str(uuid4()),
            conversation_id=conversation_id,
            role=role,
            content=content,
            agent_id=agent_id,
            agent_name=agent_name,
        )
        self.session.add(msg)
        
        conv = (
            self.session.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )
        if conv:
            conv.message_count += 1
            conv.updated_at = datetime.utcnow()
        
        self.session.commit()
        return msg

    def get_context_for_agent(
        self,
        conversation_id: str,
    ) -> dict[str, Any]:
        """Get token-efficient context for agent.
        
        Returns:
            - initiative context (Qdrant chunks)
            - conversation summary (recent messages summarized)
            - agent info
        """
        conv = (
            self.session.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )
        
        if not conv:
            return {}
        
        context = {
            "conversation_id": conv.id,
            "title": conv.title,
            "initiative_id": conv.initiative_id,
            "initiative_type": conv.initiative_type,
            "current_agent_id": conv.current_agent_id,
            "current_agent_name": conv.current_agent_name,
            "summary": conv.summary,
        }
        
        if conv.initiative_id:
            init_ctx = (
                self.session.query(InitiativeContext)
                .filter(InitiativeContext.initiative_id == conv.initiative_id)
                .first()
            )
            if init_ctx and init_ctx.expires_at > datetime.utcnow():
                context["initiative_context"] = init_ctx.context_chunks
                context["initiative_summary"] = init_ctx.summary
        
        return context

    def summarize_conversation(self, conversation_id: str) -> str | None:
        """Summarize conversation for token efficiency.
        
        Uses last N messages to create summary, marks older messages as summarized.
        """
        conv = (
            self.session.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )
        
        if not conv or conv.message_count < 10:
            return conv.summary if conv else None
        
        recent_messages = (
            self.session.query(Message)
            .filter(
                Message.conversation_id == conversation_id,
                Message.is_summarized == False,
            )
            .order_by(Message.created_at.desc())
            .limit(10)
            .all()
        )
        
        if not recent_messages:
            return conv.summary
        
        summary_text = self._create_summary(recent_messages)
        
        for msg in recent_messages:
            msg.is_summarized = True
        
        conv.summary = summary_text
        self.session.commit()
        
        return summary_text

    def _create_summary(self, messages: list[Message]) -> str:
        """Create summary from messages."""
        if not messages:
            return ""
        
        topics = []
        last_agent = None
        
        for msg in reversed(messages):
            if msg.role == "assistant" and msg.agent_name:
                last_agent = msg.agent_name
            
            if msg.role == "user" and len(msg.content) < 100:
                topics.append(msg.content)
        
        summary = f"Discussed: {', '.join(topics[:3])}"
        if last_agent:
            summary += f". Last agent: {last_agent}"
        
        return summary[:200] if summary else ""

    def cache_initiative_context(
        self,
        initiative_id: str,
        initiative_type: str,
        context_chunks: list[dict],
        ttl_seconds: int = 3600,
    ) -> InitiativeContext:
        """Cache initiative context in working memory."""
        now = datetime.utcnow()
        expires = now + timedelta(seconds=ttl_seconds)
        
        existing = (
            self.session.query(InitiativeContext)
            .filter(InitiativeContext.initiative_id == initiative_id)
            .first()
        )
        
        if existing:
            existing.context_chunks = context_chunks
            existing.cached_at = now
            existing.expires_at = expires
            existing.summary = self._summarize_chunks(context_chunks)
            self.session.commit()
            return existing
        
        context = InitiativeContext(
            id=str(uuid4()),
            initiative_id=initiative_id,
            initiative_type=initiative_type,
            context_chunks=context_chunks,
            summary=self._summarize_chunks(context_chunks),
            cached_at=now,
            expires_at=expires,
        )
        self.session.add(context)
        self.session.commit()
        
        return context

    def _summarize_chunks(self, chunks: list[dict]) -> str:
        """Summarize context chunks."""
        if not chunks:
            return ""
        
        topics = [c.get("topic", c.get("content", "")[:50]) for c in chunks[:3]]
        return f"Context: {', '.join(topics)}"

    def get_initiative_context(
        self,
        initiative_id: str,
        force_refresh: bool = False,
    ) -> InitiativeContext | None:
        """Get cached initiative context."""
        context = (
            self.session.query(InitiativeContext)
            .filter(InitiativeContext.initiative_id == initiative_id)
            .first()
        )
        
        if not context:
            return None
        
        if context.expires_at < datetime.utcnow():
            if not force_refresh:
                return None
        
        return context

    def invalidate_initiative_context(self, initiative_id: str) -> bool:
        """Invalidate cached context on initiative updates."""
        context = (
            self.session.query(InitiativeContext)
            .filter(InitiativeContext.initiative_id == initiative_id)
            .first()
        )
        
        if context:
            context.expires_at = datetime.utcnow()
            self.session.commit()
            return True
        
        return False


_chat_repo: ChatRepository | None = None


def get_chat_repository() -> ChatRepository:
    """Get chat repository instance."""
    global _chat_repo
    if _chat_repo is None:
        _chat_repo = ChatRepository(get_session().__enter__())
    return _chat_repo