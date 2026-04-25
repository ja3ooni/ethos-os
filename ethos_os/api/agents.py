"""Agent and heartbeat API endpoints."""

from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from ethos_os.db import get_session
from ethos_os.execution.heartbeat import Heartbeat
from ethos_os.execution.scheduler import AgentRegistry

router = APIRouter(prefix="/agents", tags=["agents"])


class CreateAgentRequest(BaseModel):
    """Request to create a new agent."""

    name: str = Field(..., description="Agent name")
    agent_type: str = Field(default="general", description="Agent type")
    heartbeat_interval: int = Field(default=30, ge=10, description="Heartbeat interval in seconds")
    capacity: int = Field(default=1, ge=1, description="Max concurrent tasks")


class UpdateStatusRequest(BaseModel):
    """Request to update agent status."""

    status: str = Field(..., description="New status: idle, working, blocked, complete")
    task_id: str | None = Field(default=None, description="Current task ID")
    progress_note: str | None = Field(default=None, description="Progress update")


class HeartbeatRequest(BaseModel):
    """Request to record a heartbeat."""

    status: str = Field(..., description="Current status")
    task_id: str | None = Field(default=None, description="Task being worked on")
    progress_note: str | None = Field(default=None, description="Progress update")


class AgentResponse(BaseModel):
    """Agent response model."""

    id: str
    name: str
    agent_type: str
    status: str
    heartbeat_interval: int
    current_task_id: str | None


class HeartbeatResponse(BaseModel):
    """Heartbeat response model."""

    id: str
    agent_id: str
    status: str
    task_id: str | None
    progress_note: str | None
    timestamp: str


@router.post("", response_model=AgentResponse, status_code=201)
def create_agent(request: CreateAgentRequest) -> AgentResponse:
    """Register a new agent."""
    with get_session() as session:
        registry = AgentRegistry(session)
        agent_id = str(uuid4())
        agent = registry.create(
            agent_id=agent_id,
            name=request.name,
            agent_type=request.agent_type,
            heartbeat_interval=request.heartbeat_interval,
            capacity=request.capacity,
        )
        session.commit()
        return AgentResponse(
            id=agent.id,
            name=agent.name,
            agent_type=agent.agent_type,
            status=agent.status,
            heartbeat_interval=agent.heartbeat_interval,
            current_task_id=agent.current_task_id,
        )


@router.get("", response_model=list[AgentResponse])
def list_agents() -> list[AgentResponse]:
    """List all registered agents."""
    with get_session() as session:
        registry = AgentRegistry(session)
        agents = registry.get_all()
        return [
            AgentResponse(
                id=a.id,
                name=a.name,
                agent_type=a.agent_type,
                status=a.status,
                heartbeat_interval=a.heartbeat_interval,
                current_task_id=a.current_task_id,
            )
            for a in agents
        ]


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(agent_id: str) -> AgentResponse:
    """Get an agent by ID."""
    with get_session() as session:
        registry = AgentRegistry(session)
        agent = registry.get(agent_id)
        if agent is None:
            raise HTTPException(status_code=404, detail="Agent not found")
        return AgentResponse(
            id=agent.id,
            name=agent.name,
            agent_type=agent.agent_type,
            status=agent.status,
            heartbeat_interval=agent.heartbeat_interval,
            current_task_id=agent.current_task_id,
        )


@router.get("/{agent_id}/status", response_model=dict)
def get_agent_status(agent_id: str) -> dict:
    """Get current agent status."""
    with get_session() as session:
        registry = AgentRegistry(session)
        agent = registry.get(agent_id)
        if agent is None:
            raise HTTPException(status_code=404, detail="Agent not found")
        return {
            "id": agent.id,
            "name": agent.name,
            "status": agent.status,
            "current_task_id": agent.current_task_id,
            "last_heartbeat_at": agent.last_heartbeat_at.isoformat() if agent.last_heartbeat_at else None,
            "missed_heartbeats": agent.missed_heartbeats,
        }


@router.post("/{agent_id}/heartbeat", response_model=HeartbeatResponse)
def record_heartbeat(agent_id: str, request: HeartbeatRequest) -> HeartbeatResponse:
    """Record a heartbeat for an agent."""
    with get_session() as session:
        registry = AgentRegistry(session)
        agent = registry.get(agent_id)
        if agent is None:
            raise HTTPException(status_code=404, detail="Agent not found")

        heartbeat = Heartbeat(
            id=str(uuid4()),
            agent_id=agent_id,
            status=request.status,
            task_id=request.task_id,
            progress_note=request.progress_note,
        )
        session.add(heartbeat)

        agent.status = request.status
        if request.task_id:
            agent.current_task_id = request.task_id

        session.commit()
        return HeartbeatResponse(
            id=heartbeat.id,
            agent_id=heartbeat.agent_id,
            status=heartbeat.status,
            task_id=heartbeat.task_id,
            progress_note=heartbeat.progress_note,
            timestamp=heartbeat.timestamp.isoformat(),
        )


@router.get("/{agent_id}/heartbeats", response_model=list[HeartbeatResponse])
def get_heartbeat_timeline(
    agent_id: str,
    limit: int = 100,
) -> list[HeartbeatResponse]:
    """Get heartbeat timeline for an agent."""
    with get_session() as session:
        stmt = (
            select(Heartbeat)
            .where(Heartbeat.agent_id == agent_id)
            .order_by(Heartbeat.timestamp.desc())
            .limit(limit)
        )
        heartbeats = list(session.execute(stmt).scalars().all())

        return [
            HeartbeatResponse(
                id=h.id,
                agent_id=h.agent_id,
                status=h.status,
                task_id=h.task_id,
                progress_note=h.progress_note,
                timestamp=h.timestamp.isoformat(),
            )
            for h in heartbeats
        ]


@router.patch("/{agent_id}", response_model=AgentResponse)
def update_agent_status(agent_id: str, request: UpdateStatusRequest) -> AgentResponse:
    """Update agent status."""
    with get_session() as session:
        registry = AgentRegistry(session)
        agent = registry.get(agent_id)
        if agent is None:
            raise HTTPException(status_code=404, detail="Agent not found")

        agent.status = request.status
        if request.task_id:
            agent.current_task_id = request.task_id

        session.commit()
        return AgentResponse(
            id=agent.id,
            name=agent.name,
            agent_type=agent.agent_type,
            status=agent.status,
            heartbeat_interval=agent.heartbeat_interval,
            current_task_id=agent.current_task_id,
        )