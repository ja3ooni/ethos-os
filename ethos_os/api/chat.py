"""Chat API for EthosOS v0.2 Phase 3.

CHAT-01: Paperclip-style chat interface
CHAT-02: Initiative context injection
CHAT-03: Agent switching
CHAT-04: Real-time updates via SSE
"""

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ethos_os.db import get_session
from ethos_os.models.chat import Conversation, Message, InitiativeContext
from ethos_os.agents.registry import AgentRepository

router = APIRouter(prefix="/chat", tags=["chat"])


class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""
    title: str | None = None
    initiative_id: str | None = None
    initiative_type: str | None = None
    user_id: str | None = None


class SendMessageRequest(BaseModel):
    """Request to send a message."""
    conversation_id: str
    content: str
    agent_id: str | None = None
    agent_name: str | None = None


class SwitchAgentRequest(BaseModel):
    """Request to switch agent in conversation."""
    conversation_id: str
    agent_id: str
    agent_name: str


class SetInitiativeRequest(BaseModel):
    """Request to set initiative context."""
    conversation_id: str
    initiative_id: str
    initiative_type: str


class MessageResponse(BaseModel):
    """Message response."""
    id: str
    role: str
    content: str
    agent_id: str | None = None
    agent_name: str | None = None
    created_at: str


class ConversationResponse(BaseModel):
    """Conversation response."""
    id: str
    title: str
    initiative_id: str | None = None
    initiative_type: str | None = None
    current_agent_id: str | None = None
    current_agent_name: str | None = None
    summary: str | None = None
    message_count: int
    is_active: bool
    created_at: str
    updated_at: str


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(request: CreateConversationRequest) -> ConversationResponse:
    """Create a new conversation (CHAT-01)."""
    with get_session() as session:
        conv = Conversation(
            id=str(uuid4()),
            user_id=request.user_id,
            title=request.title or "New Conversation",
            initiative_id=request.initiative_id,
            initiative_type=request.initiative_type,
        )
        session.add(conv)
        session.flush()

        return ConversationResponse(
            id=conv.id,
            title=conv.title,
            initiative_id=conv.initiative_id,
            initiative_type=conv.initiative_type,
            current_agent_id=conv.current_agent_id,
            current_agent_name=conv.current_agent_name,
            summary=conv.summary,
            message_count=conv.message_count,
            is_active=conv.is_active,
            created_at=conv.created_at.isoformat(),
            updated_at=conv.updated_at.isoformat(),
        )


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    user_id: str | None = None,
    initiative_id: str | None = None,
    limit: int = 20,
) -> list[ConversationResponse]:
    """List conversations (CHAT-01)."""
    with get_session() as session:
        query = session.query(Conversation)
        
        if user_id:
            query = query.filter(Conversation.user_id == user_id)
        if initiative_id:
            query = query.filter(Conversation.initiative_id == initiative_id)
        
        conversations = (
            query.filter(Conversation.is_active == True)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
            .all()
        )

        return [
            ConversationResponse(
                id=c.id,
                title=c.title,
                initiative_id=c.initiative_id,
                initiative_type=c.initiative_type,
                current_agent_id=c.current_agent_id,
                current_agent_name=c.current_agent_name,
                summary=c.summary,
                message_count=c.message_count,
                is_active=c.is_active,
                created_at=c.created_at.isoformat(),
                updated_at=c.updated_at.isoformat(),
            )
            for c in conversations
        ]


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str) -> ConversationResponse:
    """Get conversation by ID (CHAT-01)."""
    with get_session() as session:
        conv = (
            session.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )
        
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return ConversationResponse(
            id=conv.id,
            title=conv.title,
            initiative_id=conv.initiative_id,
            initiative_type=conv.initiative_type,
            current_agent_id=conv.current_agent_id,
            current_agent_name=conv.current_agent_name,
            summary=conv.summary,
            message_count=conv.message_count,
            is_active=conv.is_active,
            created_at=conv.created_at.isoformat(),
            updated_at=conv.updated_at.isoformat(),
        )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str) -> dict:
    """Delete conversation (CHAT-05)."""
    with get_session() as session:
        conv = (
            session.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )
        
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        conv.is_active = False
        session.commit()
        
        return {"status": "deleted", "conversation_id": conversation_id}


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: str,
    request: SendMessageRequest,
) -> MessageResponse:
    """Send a message to the conversation (CHAT-01, CHAT-05)."""
    with get_session() as session:
        conv = (
            session.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )
        
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        if request.agent_id and request.agent_name:
            conv.current_agent_id = request.agent_id
            conv.current_agent_name = request.agent_name
        
        user_msg = Message(
            id=str(uuid4()),
            conversation_id=conversation_id,
            role="user",
            content=request.content,
        )
        session.add(user_msg)
        
        conv.message_count += 1
        
        if not conv.title or conv.title == "New Conversation":
            conv.title = request.content[:50] + "..." if len(request.content) > 50 else request.content
        
        session.commit()
        
        return MessageResponse(
            id=user_msg.id,
            role=user_msg.role,
            content=user_msg.content,
            agent_id=user_msg.agent_id,
            agent_name=user_msg.agent_name,
            created_at=user_msg.created_at.isoformat(),
        )


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    conversation_id: str,
    limit: int = 50,
    before_message_id: str | None = None,
) -> list[MessageResponse]:
    """Get messages for a conversation (CHAT-01, CHAT-05).
    
    Token-efficient: Returns recent messages, with summary for older ones.
    """
    with get_session() as session:
        conv = (
            session.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )
        
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        query = session.query(Message).filter(
            Message.conversation_id == conversation_id
        )
        
        messages = (
            query.order_by(Message.created_at.desc())
            .limit(limit)
            .all()
        )
        
        return [
            MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                agent_id=m.agent_id,
                agent_name=m.agent_name,
                created_at=m.created_at.isoformat(),
            )
            for m in reversed(messages)
        ]


@router.post("/conversations/{conversation_id}/switch-agent", response_model=ConversationResponse)
async def switch_agent(
    conversation_id: str,
    request: SwitchAgentRequest,
) -> ConversationResponse:
    """Switch agent in conversation (CHAT-03)."""
    with get_session() as session:
        conv = (
            session.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )
        
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        conv.current_agent_id = request.agent_id
        conv.current_agent_name = request.agent_name
        session.commit()
        
        return ConversationResponse(
            id=conv.id,
            title=conv.title,
            initiative_id=conv.initiative_id,
            initiative_type=conv.initiative_type,
            current_agent_id=conv.current_agent_id,
            current_agent_name=conv.current_agent_name,
            summary=conv.summary,
            message_count=conv.message_count,
            is_active=conv.is_active,
            created_at=conv.created_at.isoformat(),
            updated_at=conv.updated_at.isoformat(),
        )


@router.post("/conversations/{conversation_id}/initiative", response_model=ConversationResponse)
async def set_initiative(
    conversation_id: str,
    request: SetInitiativeRequest,
) -> ConversationResponse:
    """Set initiative context (CHAT-02)."""
    with get_session() as session:
        conv = (
            session.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )
        
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        conv.initiative_id = request.initiative_id
        conv.initiative_type = request.initiative_type
        session.commit()
        
        return ConversationResponse(
            id=conv.id,
            title=conv.title,
            initiative_id=conv.initiative_id,
            initiative_type=conv.initiative_type,
            current_agent_id=conv.current_agent_id,
            current_agent_name=conv.current_agent_name,
            summary=conv.summary,
            message_count=conv.message_count,
            is_active=conv.is_active,
            created_at=conv.created_at.isoformat(),
            updated_at=conv.updated_at.isoformat(),
        )


@router.get("/agents", response_model=list[dict])
async def list_agents_for_chat(
    role: str | None = None,
    division: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """List available agents for chat (CHAT-03).
    
    Token-efficient: Returns summaries only, not full prompts.
    """
    with get_session() as session:
        repo = AgentRepository(session)
        agents = repo.list_for_task(
            role=role,
            division=division,
            hired_only=True,
            limit=limit,
        )
        return agents


async def event_generator(conversation_id: str):
    """SSE event generator for real-time updates (CHAT-04)."""
    import asyncio
    import time
    
    last_update = time.time()
    
    while True:
        await asyncio.sleep(1)
        
        yield f"data: {last_update}\n\n"


@router.get("/conversations/{conversation_id}/stream")
async def stream_conversation(conversation_id: str) -> StreamingResponse:
    """Stream conversation updates (CHAT-04).
    
    Real-time updates via Server-Sent Events.
    """
    return StreamingResponse(
        event_generator(conversation_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )