"""Agent management API endpoints."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from ethos_os.db import get_session
from ethos_os.agents.registry import AgentRepository, import_agents_from_agency_repo
from ethos_os.agents.executor import AgentExecutor

router = APIRouter(prefix="/agents", tags=["agents"])
executor = AgentExecutor()


class AgentListResponse(BaseModel):
    agents: list[dict]
    total: int


class AgentHireRequest(BaseModel):
    source_path: str
    name: str
    role: str
    division: str
    skills_summary: str
    capabilities: list[str]
    specialization: Optional[str] = None
    max_monthly_budget_usd: Optional[str] = None


class AgentExecutionRequest(BaseModel):
    agent_id: str
    task_prompt: str
    context: Optional[dict] = None


@router.get("/", response_model=AgentListResponse)
def list_agents(
    role: Optional[str] = Query(None, description="Filter by role (ceo, lead, execution, etc.)"),
    division: Optional[str] = Query(None, description="Filter by division (engineering, sales, etc.)"),
    capabilities: Optional[str] = Query(None, description="Comma-separated capabilities to filter by"),
    hired_only: bool = Query(True, description="Only show hired agents"),
    limit: int = Query(20, le=100),
):
    """List agents for task assignment - TOKEN EFFICIENT.

    Returns summary only, NOT full prompts.
    Use this for UI listings and task assignment.
    """
    caps = capabilities.split(",") if capabilities else None

    agents = executor.list_agents_for_task(
        task_requirements=caps or [],
        role=role,
        division=division,
    )

    return AgentListResponse(agents=agents[:limit], total=len(agents))


@router.get("/search")
def search_agents(
    query: str = Query(..., description="Search query for capabilities"),
    limit: int = Query(10, le=50),
):
    """Search agents by capability - TOKEN EFFICIENT."""
    repo = AgentRepository(get_session().__enter__())
    agents = repo.search_by_capability(query, limit)
    return {"agents": agents, "query": query}


@router.get("/{agent_id}")
def get_agent(agent_id: str):
    """Get agent details for execution.

    Returns full config including prompt_reference.
    Only use this when executing, not for listings.
    """
    repo = AgentRepository(get_session().__enter__())
    agent = repo.get_for_execution(agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return agent


@router.post("/hire")
def hire_agent(request: AgentHireRequest):
    """Hire an agent into this company."""
    repo = AgentRepository(get_session().__enter__())

    agent = repo.hire(
        source_path=request.source_path,
        name=request.name,
        role=request.role,
        division=request.division,
        skills_summary=request.skills_summary,
        capabilities=request.capabilities,
        specialization=request.specialization,
        max_monthly_budget_usd=request.max_monthly_budget_usd,
    )

    return {
        "id": agent.id,
        "name": agent.name,
        "role": agent.role,
        "status": "hired",
        "hired_at": agent.hired_at.isoformat() if agent.hired_at else None,
    }


@router.post("/fire/{agent_id}")
def fire_agent(agent_id: str):
    """Terminate an agent."""
    repo = AgentRepository(get_session().__enter__())

    if repo.fire(agent_id):
        return {"agent_id": agent_id, "status": "fired"}
    else:
        raise HTTPException(status_code=404, detail="Agent not found")


@router.post("/execute")
def execute_agent_task(request: AgentExecutionRequest):
    """Execute a task with an agent - TOKEN EFFICIENT.

    Only injects relevant context, not full history.
    """
    result = executor.execute_task(
        agent_id=request.agent_id,
        task_prompt=request.task_prompt,
        context=request.context,
    )

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.post("/import-from-repo")
def import_agents(
    repo_path: str = Query(..., description="Path to agency-agents repository"),
):
    """Import agents from agency-agents repo.

    Parses only YAML frontmatter - TOKEN EFFICIENT.
    Does NOT import full prompts, only summaries.
    """
    try:
        count = import_agents_from_agency_repo(repo_path)
        return {"imported": count, "status": "complete"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))