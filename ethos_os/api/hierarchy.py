"""Initiative hierarchy API - CRUD for portfolio, program, project, sprint, task."""

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from ethos_os.db import get_session
from ethos_os.models.portfolio import Portfolio
from ethos_os.models.program import Program
from ethos_os.models.project import Project
from ethos_os.models.sprint import Sprint, SprintStatus
from ethos_os.models.task import Task
from ethos_os.repositories.portfolio import PortfolioRepository
from ethos_os.repositories.program import ProgramRepository
from ethos_os.repositories.project import ProjectRepository
from ethos_os.repositories.sprint import SprintRepository
from ethos_os.repositories.task import TaskRepository

router = APIRouter(prefix="/hierarchy", tags=["initiative hierarchy"])


# Request/Response Models
class PortfolioCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    strategic_intent: str | None = None
    owner_id: str | None = None


class PortfolioResponse(BaseModel):
    id: str
    name: str
    strategic_intent: str | None
    owner_id: str | None
    path: str
    path_depth: int
    created_at: str | None
    updated_at: str | None

    model_config = ConfigDict(from_attributes=True)


class ProgramCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    portfolio_id: str = Field(..., description="Parent portfolio ID")
    owner_id: str | None = None


class ProgramResponse(BaseModel):
    id: str
    name: str
    description: str | None
    portfolio_id: str
    owner_id: str | None
    path: str
    path_depth: int
    created_at: str | None
    updated_at: str | None

    model_config = ConfigDict(from_attributes=True)


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    program_id: str = Field(..., description="Parent program ID")
    intent: str | None = None
    success_metric: str | None = None
    scope: str | None = None
    boundaries: str | None = None
    budget: int | None = None
    owner_id: str | None = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    program_id: str
    prd_status: str
    intent: str | None
    success_metric: str | None
    scope: str | None
    boundaries: str | None
    budget: int | None
    owner_id: str | None
    path: str
    path_depth: int
    created_at: str | None
    updated_at: str | None

    model_config = ConfigDict(from_attributes=True)


class ProjectUpdate(BaseModel):
    name: str | None = None
    intent: str | None = None
    success_metric: str | None = None
    scope: str | None = None
    boundaries: str | None = None
    budget: int | None = None
    prd_status: str | None = None


class SprintCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    project_id: str = Field(..., description="Parent project ID")
    goal: str | None = None
    start_date: str | None = Field(None, description="ISO date string")
    end_date: str | None = Field(None, description="ISO date string")
    capacity_hours: int | None = None
    owner_id: str | None = None


class SprintResponse(BaseModel):
    id: str
    name: str
    project_id: str
    goal: str | None
    start_date: str | None
    end_date: str | None
    capacity_hours: int | None
    status: str
    owner_id: str | None
    path: str
    path_depth: int
    created_at: str | None
    updated_at: str | None

    model_config = ConfigDict(from_attributes=True)


class SprintUpdate(BaseModel):
    name: str | None = None
    goal: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    capacity_hours: int | None = None
    status: str | None = None


class TaskCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    sprint_id: str = Field(..., description="Parent sprint ID")
    prd_scope_item_id: str = Field(..., description="PRD scope reference (required - D-44)")
    effort_estimate_hours: float | None = None
    assignee_id: str | None = None
    description: str | None = None
    owner_id: str | None = None


class TaskResponse(BaseModel):
    id: str
    name: str
    sprint_id: str
    prd_scope_item_id: str
    effort_estimate_hours: float | None
    assignee_id: str | None
    status: str
    description: str | None
    owner_id: str | None
    path: str
    path_depth: int
    created_at: str | None
    updated_at: str | None

    model_config = ConfigDict(from_attributes=True)


class TaskUpdate(BaseModel):
    name: str | None = None
    effort_estimate_hours: float | None = None
    assignee_id: str | None = None
    status: str | None = None
    description: str | None = None


class LineageResponse(BaseModel):
    portfolio: dict | None
    program: dict | None
    project: dict | None
    sprint: dict | None
    task: dict


class TreeNode(BaseModel):
    id: str
    name: str
    type: str
    status: str | None = None
    path_depth: int
    children: list["TreeNode"] = Field(default_factory=list)


def _entity_to_dict(entity: Any) -> dict | None:
    if entity is None:
        return None
    return {
        "id": entity.id,
        "name": getattr(entity, "name", None),
        "status": getattr(entity, "prd_status", None) or getattr(entity, "status", None),
        "path": getattr(entity, "path", None),
    }


# Portfolio Endpoints
@router.post("/portfolios", response_model=PortfolioResponse, status_code=201, summary="Create portfolio")
def create_portfolio(request: PortfolioCreate) -> PortfolioResponse:
    """Create a new portfolio (company or strategic entity)."""
    with get_session() as session:
        repo = PortfolioRepository(session)
        portfolio_id = str(uuid4())
        portfolio = repo.create({
            "id": portfolio_id,
            "name": request.name,
            "strategic_intent": request.strategic_intent,
            "owner_id": request.owner_id,
            "path": f"/{portfolio_id}/",
            "path_depth": 1,
            "parent_id": None,
        })
        session.commit()
        return PortfolioResponse(
            id=portfolio.id,
            name=portfolio.name,
            strategic_intent=portfolio.strategic_intent,
            owner_id=portfolio.owner_id,
            path=portfolio.path,
            path_depth=portfolio.path_depth,
            created_at=portfolio.created_at.isoformat() if portfolio.created_at else None,
            updated_at=portfolio.updated_at.isoformat() if portfolio.updated_at else None,
        )


@router.get("/portfolios", response_model=list[PortfolioResponse], summary="List portfolios")
def list_portfolios(
    owner_id: str | None = Query(None, description="Filter by owner"),
) -> list[PortfolioResponse]:
    """List all portfolios, optionally filtered by owner."""
    with get_session() as session:
        repo = PortfolioRepository(session)
        if owner_id:
            portfolios = repo.list_by_owner(owner_id)
        else:
            portfolios = repo.list()
        return [
            PortfolioResponse(
                id=p.id, name=p.name, strategic_intent=p.strategic_intent,
                owner_id=p.owner_id, path=p.path, path_depth=p.path_depth,
                created_at=p.created_at.isoformat() if p.created_at else None,
                updated_at=p.updated_at.isoformat() if p.updated_at else None,
            )
            for p in portfolios
        ]


@router.get("/portfolios/{portfolio_id}", response_model=PortfolioResponse, summary="Get portfolio")
def get_portfolio(portfolio_id: str) -> PortfolioResponse:
    """Get a portfolio by ID."""
    with get_session() as session:
        repo = PortfolioRepository(session)
        portfolio = repo.get(portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        return PortfolioResponse(
            id=portfolio.id, name=portfolio.name, strategic_intent=portfolio.strategic_intent,
            owner_id=portfolio.owner_id, path=portfolio.path, path_depth=portfolio.path_depth,
            created_at=portfolio.created_at.isoformat() if portfolio.created_at else None,
            updated_at=portfolio.updated_at.isoformat() if portfolio.updated_at else None,
        )


# Program Endpoints
@router.post("/programs", response_model=ProgramResponse, status_code=201, summary="Create program")
def create_program(request: ProgramCreate) -> ProgramResponse:
    """Create a new program within a portfolio."""
    with get_session() as session:
        repo = ProgramRepository(session)
        program_id = str(uuid4())
        try:
            program = repo.create({
                "id": program_id,
                "name": request.name,
                "description": request.description,
                "portfolio_id": request.portfolio_id,
                "owner_id": request.owner_id,
            })
            session.commit()
        except KeyError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return ProgramResponse(
            id=program.id, name=program.name, description=program.description,
            portfolio_id=program.portfolio_id, owner_id=program.owner_id,
            path=program.path, path_depth=program.path_depth,
            created_at=program.created_at.isoformat() if program.created_at else None,
            updated_at=program.updated_at.isoformat() if program.updated_at else None,
        )


@router.get("/programs", response_model=list[ProgramResponse], summary="List programs")
def list_programs(
    portfolio_id: str | None = Query(None, description="Filter by portfolio"),
) -> list[ProgramResponse]:
    """List all programs, optionally filtered by portfolio."""
    with get_session() as session:
        repo = ProgramRepository(session)
        if portfolio_id:
            programs = repo.list_by_portfolio(portfolio_id)
        else:
            programs = repo.list()
        return [
            ProgramResponse(
                id=p.id, name=p.name, description=p.description,
                portfolio_id=p.portfolio_id, owner_id=p.owner_id,
                path=p.path, path_depth=p.path_depth,
                created_at=p.created_at.isoformat() if p.created_at else None,
                updated_at=p.updated_at.isoformat() if p.updated_at else None,
            )
            for p in programs
        ]


@router.get("/programs/{program_id}", response_model=ProgramResponse, summary="Get program")
def get_program(program_id: str) -> ProgramResponse:
    """Get a program by ID."""
    with get_session() as session:
        repo = ProgramRepository(session)
        program = repo.get(program_id)
        if not program:
            raise HTTPException(status_code=404, detail="Program not found")
        return ProgramResponse(
            id=program.id, name=program.name, description=program.description,
            portfolio_id=program.portfolio_id, owner_id=program.owner_id,
            path=program.path, path_depth=program.path_depth,
            created_at=program.created_at.isoformat() if program.created_at else None,
            updated_at=program.updated_at.isoformat() if program.updated_at else None,
        )


# Project Endpoints
@router.post("/projects", response_model=ProjectResponse, status_code=201, summary="Create project")
def create_project(request: ProjectCreate) -> ProjectResponse:
    """Create a new project within a program. Requires board-reviewed PRD."""
    with get_session() as session:
        repo = ProjectRepository(session)
        project_id = str(uuid4())
        try:
            project = repo.create({
                "id": project_id,
                "name": request.name,
                "program_id": request.program_id,
                "intent": request.intent,
                "success_metric": request.success_metric,
                "scope": request.scope,
                "boundaries": request.boundaries,
                "budget": request.budget,
                "owner_id": request.owner_id,
            })
            session.commit()
        except KeyError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return ProjectResponse(
            id=project.id, name=project.name, program_id=project.program_id,
            prd_status=project.prd_status, intent=project.intent,
            success_metric=project.success_metric, scope=project.scope,
            boundaries=project.boundaries, budget=project.budget,
            owner_id=project.owner_id, path=project.path, path_depth=project.path_depth,
            created_at=project.created_at.isoformat() if project.created_at else None,
            updated_at=project.updated_at.isoformat() if project.updated_at else None,
        )


@router.get("/projects", response_model=list[ProjectResponse], summary="List projects")
def list_projects(
    program_id: str | None = Query(None, description="Filter by program"),
    status: str | None = Query(None, description="Filter by PRD status"),
    search: str | None = Query(None, description="Search by name"),
) -> list[ProjectResponse]:
    """List all projects with optional filters."""
    with get_session() as session:
        repo = ProjectRepository(session)
        if search:
            projects = repo.search_by_name(search)
        elif program_id:
            projects = repo.list_by_program(program_id)
        elif status:
            projects = repo.list_by_status(status)
        else:
            projects = repo.list()
        return [
            ProjectResponse(
                id=p.id, name=p.name, program_id=p.program_id,
                prd_status=p.prd_status, intent=p.intent,
                success_metric=p.success_metric, scope=p.scope,
                boundaries=p.boundaries, budget=p.budget,
                owner_id=p.owner_id, path=p.path, path_depth=p.path_depth,
                created_at=p.created_at.isoformat() if p.created_at else None,
                updated_at=p.updated_at.isoformat() if p.updated_at else None,
            )
            for p in projects
        ]


@router.get("/projects/approved", response_model=list[ProjectResponse], summary="List approved projects")
def list_approved_projects() -> list[ProjectResponse]:
    """List all projects with approved PRD (ready for sprints)."""
    with get_session() as session:
        repo = ProjectRepository(session)
        projects = repo.list_approved()
        return [
            ProjectResponse(
                id=p.id, name=p.name, program_id=p.program_id,
                prd_status=p.prd_status, intent=p.intent,
                success_metric=p.success_metric, scope=p.scope,
                boundaries=p.boundaries, budget=p.budget,
                owner_id=p.owner_id, path=p.path, path_depth=p.path_depth,
                created_at=p.created_at.isoformat() if p.created_at else None,
                updated_at=p.updated_at.isoformat() if p.updated_at else None,
            )
            for p in projects
        ]


@router.get("/projects/{project_id}", response_model=ProjectResponse, summary="Get project")
def get_project(project_id: str) -> ProjectResponse:
    """Get a project by ID."""
    with get_session() as session:
        repo = ProjectRepository(session)
        project = repo.get(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return ProjectResponse(
            id=project.id, name=project.name, program_id=project.program_id,
            prd_status=project.prd_status, intent=project.intent,
            success_metric=project.success_metric, scope=project.scope,
            boundaries=project.boundaries, budget=project.budget,
            owner_id=project.owner_id, path=project.path, path_depth=project.path_depth,
            created_at=project.created_at.isoformat() if project.created_at else None,
            updated_at=project.updated_at.isoformat() if project.updated_at else None,
        )


@router.patch("/projects/{project_id}", response_model=ProjectResponse, summary="Update project")
def update_project(project_id: str, request: ProjectUpdate) -> ProjectResponse:
    """Update a project."""
    with get_session() as session:
        repo = ProjectRepository(session)
        project = repo.get(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        updates = {k: v for k, v in request.model_dump().items() if v is not None}
        if updates:
            for key, value in updates.items():
                setattr(project, key, value)
            session.commit()

        return ProjectResponse(
            id=project.id, name=project.name, program_id=project.program_id,
            prd_status=project.prd_status, intent=project.intent,
            success_metric=project.success_metric, scope=project.scope,
            boundaries=project.boundaries, budget=project.budget,
            owner_id=project.owner_id, path=project.path, path_depth=project.path_depth,
            created_at=project.created_at.isoformat() if project.created_at else None,
            updated_at=project.updated_at.isoformat() if project.updated_at else None,
        )


# Sprint Endpoints
@router.post("/sprints", response_model=SprintResponse, status_code=201, summary="Create sprint")
def create_sprint(request: SprintCreate) -> SprintResponse:
    """Create a new sprint within a project. Project must have approved PRD (HIER-06)."""
    with get_session() as session:
        repo = SprintRepository(session)
        sprint_id = str(uuid4())
        try:
            sprint = repo.create({
                "id": sprint_id,
                "name": request.name,
                "project_id": request.project_id,
                "goal": request.goal,
                "start_date": request.start_date,
                "end_date": request.end_date,
                "capacity_hours": request.capacity_hours,
                "owner_id": request.owner_id,
            })
            session.commit()
        except KeyError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return SprintResponse(
            id=sprint.id, name=sprint.name, project_id=sprint.project_id,
            goal=sprint.goal, start_date=sprint.start_date, end_date=sprint.end_date,
            capacity_hours=sprint.capacity_hours, status=sprint.status,
            owner_id=sprint.owner_id, path=sprint.path, path_depth=sprint.path_depth,
            created_at=sprint.created_at.isoformat() if sprint.created_at else None,
            updated_at=sprint.updated_at.isoformat() if sprint.updated_at else None,
        )


@router.get("/sprints", response_model=list[SprintResponse], summary="List sprints")
def list_sprints(
    project_id: str | None = Query(None, description="Filter by project"),
    status: str | None = Query(None, description="Filter by status"),
) -> list[SprintResponse]:
    """List all sprints with optional filters."""
    with get_session() as session:
        repo = SprintRepository(session)
        if project_id:
            sprints = repo.list_by_project(project_id)
        elif status == SprintStatus.ACTIVE.value:
            sprints = repo.list_active()
        else:
            sprints = repo.list()
        return [
            SprintResponse(
                id=s.id, name=s.name, project_id=s.project_id,
                goal=s.goal, start_date=s.start_date, end_date=s.end_date,
                capacity_hours=s.capacity_hours, status=s.status,
                owner_id=s.owner_id, path=s.path, path_depth=s.path_depth,
                created_at=s.created_at.isoformat() if s.created_at else None,
                updated_at=s.updated_at.isoformat() if s.updated_at else None,
            )
            for s in sprints
        ]


@router.get("/sprints/{sprint_id}", response_model=SprintResponse, summary="Get sprint")
def get_sprint(sprint_id: str) -> SprintResponse:
    """Get a sprint by ID."""
    with get_session() as session:
        repo = SprintRepository(session)
        sprint = repo.get(sprint_id)
        if not sprint:
            raise HTTPException(status_code=404, detail="Sprint not found")
        return SprintResponse(
            id=sprint.id, name=sprint.name, project_id=sprint.project_id,
            goal=sprint.goal, start_date=sprint.start_date, end_date=sprint.end_date,
            capacity_hours=sprint.capacity_hours, status=sprint.status,
            owner_id=sprint.owner_id, path=sprint.path, path_depth=sprint.path_depth,
            created_at=sprint.created_at.isoformat() if sprint.created_at else None,
            updated_at=sprint.updated_at.isoformat() if sprint.updated_at else None,
        )


@router.patch("/sprints/{sprint_id}", response_model=SprintResponse, summary="Update sprint")
def update_sprint(sprint_id: str, request: SprintUpdate) -> SprintResponse:
    """Update a sprint."""
    with get_session() as session:
        repo = SprintRepository(session)
        sprint = repo.get(sprint_id)
        if not sprint:
            raise HTTPException(status_code=404, detail="Sprint not found")

        updates = {k: v for k, v in request.model_dump().items() if v is not None}
        if updates:
            for key, value in updates.items():
                setattr(sprint, key, value)
            session.commit()

        return SprintResponse(
            id=sprint.id, name=sprint.name, project_id=sprint.project_id,
            goal=sprint.goal, start_date=sprint.start_date, end_date=sprint.end_date,
            capacity_hours=sprint.capacity_hours, status=sprint.status,
            owner_id=sprint.owner_id, path=sprint.path, path_depth=sprint.path_depth,
            created_at=sprint.created_at.isoformat() if sprint.created_at else None,
            updated_at=sprint.updated_at.isoformat() if sprint.updated_at else None,
        )


# Task Endpoints
@router.post("/tasks", response_model=TaskResponse, status_code=201, summary="Create task")
def create_task(request: TaskCreate) -> TaskResponse:
    """Create a new task within a sprint. Requires prd_scope_item_id (HIER-11, D-44)."""
    with get_session() as session:
        repo = TaskRepository(session)
        task_id = str(uuid4())
        try:
            task = repo.create({
                "id": task_id,
                "name": request.name,
                "sprint_id": request.sprint_id,
                "prd_scope_item_id": request.prd_scope_item_id,
                "effort_estimate_hours": request.effort_estimate_hours,
                "assignee_id": request.assignee_id,
                "description": request.description,
                "owner_id": request.owner_id,
            })
            session.commit()
        except KeyError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return TaskResponse(
            id=task.id, name=task.name, sprint_id=task.sprint_id,
            prd_scope_item_id=task.prd_scope_item_id,
            effort_estimate_hours=float(task.effort_estimate_hours) if task.effort_estimate_hours else None,
            assignee_id=task.assignee_id, status=task.status,
            description=task.description, owner_id=task.owner_id,
            path=task.path, path_depth=task.path_depth,
            created_at=task.created_at.isoformat() if task.created_at else None,
            updated_at=task.updated_at.isoformat() if task.updated_at else None,
        )


@router.get("/tasks", response_model=list[TaskResponse], summary="List tasks")
def list_tasks(
    sprint_id: str | None = Query(None, description="Filter by sprint"),
    assignee_id: str | None = Query(None, description="Filter by assignee"),
    status: str | None = Query(None, description="Filter by status"),
    prd_scope_item_id: str | None = Query(None, description="Filter by PRD scope item"),
) -> list[TaskResponse]:
    """List all tasks with optional filters."""
    with get_session() as session:
        repo = TaskRepository(session)
        if sprint_id:
            tasks = repo.list_by_sprint(sprint_id)
        elif assignee_id:
            tasks = repo.list_by_assignee(assignee_id)
        elif status:
            tasks = repo.list_by_status(status)
        elif prd_scope_item_id:
            tasks = repo.get_by_prd_scope(prd_scope_item_id)
        else:
            tasks = repo.list()
        return [
            TaskResponse(
                id=t.id, name=t.name, sprint_id=t.sprint_id,
                prd_scope_item_id=t.prd_scope_item_id,
                effort_estimate_hours=float(t.effort_estimate_hours) if t.effort_estimate_hours else None,
                assignee_id=t.assignee_id, status=t.status,
                description=t.description, owner_id=t.owner_id,
                path=t.path, path_depth=t.path_depth,
                created_at=t.created_at.isoformat() if t.created_at else None,
                updated_at=t.updated_at.isoformat() if t.updated_at else None,
            )
            for t in tasks
        ]


@router.get("/tasks/{task_id}", response_model=TaskResponse, summary="Get task")
def get_task(task_id: str) -> TaskResponse:
    """Get a task by ID."""
    with get_session() as session:
        repo = TaskRepository(session)
        task = repo.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return TaskResponse(
            id=task.id, name=task.name, sprint_id=task.sprint_id,
            prd_scope_item_id=task.prd_scope_item_id,
            effort_estimate_hours=float(task.effort_estimate_hours) if task.effort_estimate_hours else None,
            assignee_id=task.assignee_id, status=task.status,
            description=task.description, owner_id=task.owner_id,
            path=task.path, path_depth=task.path_depth,
            created_at=task.created_at.isoformat() if task.created_at else None,
            updated_at=task.updated_at.isoformat() if task.updated_at else None,
        )


@router.patch("/tasks/{task_id}", response_model=TaskResponse, summary="Update task")
def update_task(task_id: str, request: TaskUpdate) -> TaskResponse:
    """Update a task."""
    with get_session() as session:
        repo = TaskRepository(session)
        task = repo.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        updates = {k: v for k, v in request.model_dump().items() if v is not None}
        if updates:
            for key, value in updates.items():
                setattr(task, key, value)
            session.commit()

        return TaskResponse(
            id=task.id, name=task.name, sprint_id=task.sprint_id,
            prd_scope_item_id=task.prd_scope_item_id,
            effort_estimate_hours=float(task.effort_estimate_hours) if task.effort_estimate_hours else None,
            assignee_id=task.assignee_id, status=task.status,
            description=task.description, owner_id=task.owner_id,
            path=task.path, path_depth=task.path_depth,
            created_at=task.created_at.isoformat() if task.created_at else None,
            updated_at=task.updated_at.isoformat() if task.updated_at else None,
        )


# Lineage Endpoints
@router.get("/portfolios/{portfolio_id}/lineage", response_model=dict, summary="Get portfolio lineage")
def get_portfolio_lineage(portfolio_id: str) -> dict:
    """Get portfolio lineage (returns portfolio itself for root level)."""
    with get_session() as session:
        portfolio = session.get(Portfolio, portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        return {"portfolio": _entity_to_dict(portfolio)}


@router.get("/programs/{program_id}/lineage", response_model=LineageResponse, summary="Get program lineage")
def get_program_lineage(program_id: str) -> LineageResponse:
    """Get program lineage (program + portfolio)."""
    with get_session() as session:
        repo = ProgramRepository(session)
        lineage = repo.get_lineage(program_id)
        return LineageResponse(
            portfolio=_entity_to_dict(lineage.get("portfolio")),
            program=_entity_to_dict(lineage.get("program")),
            project=None,
            sprint=None,
            task=None,
        )


@router.get("/projects/{project_id}/lineage", response_model=LineageResponse, summary="Get project lineage")
def get_project_lineage(project_id: str) -> LineageResponse:
    """Get project lineage (project + program + portfolio)."""
    with get_session() as session:
        repo = ProjectRepository(session)
        lineage = repo.get_with_lineage(project_id)
        return LineageResponse(
            portfolio=_entity_to_dict(lineage.get("portfolio")),
            program=_entity_to_dict(lineage.get("program")),
            project=_entity_to_dict(lineage.get("project")),
            sprint=None,
            task=None,
        )


@router.get("/sprints/{sprint_id}/lineage", response_model=LineageResponse, summary="Get sprint lineage")
def get_sprint_lineage(sprint_id: str) -> LineageResponse:
    """Get sprint lineage (sprint + project + program + portfolio)."""
    with get_session() as session:
        repo = SprintRepository(session)
        lineage = repo.get_lineage(sprint_id)
        return LineageResponse(
            portfolio=_entity_to_dict(lineage.get("portfolio")),
            program=_entity_to_dict(lineage.get("program")),
            project=_entity_to_dict(lineage.get("project")),
            sprint=_entity_to_dict(lineage.get("sprint")),
            task=None,
        )


@router.get("/tasks/{task_id}/lineage", response_model=LineageResponse, summary="Get task lineage")
def get_task_lineage(task_id: str) -> LineageResponse:
    """Get task lineage (task + sprint + project + program + portfolio) (HIER-10)."""
    with get_session() as session:
        repo = TaskRepository(session)
        lineage = repo.get_lineage(task_id)
        return LineageResponse(
            portfolio=_entity_to_dict(lineage.get("portfolio")),
            program=_entity_to_dict(lineage.get("program")),
            project=_entity_to_dict(lineage.get("project")),
            sprint=_entity_to_dict(lineage.get("sprint")),
            task=_entity_to_dict(lineage.get("task")),
        )


# Tree View
@router.get("/tree", response_model=list[TreeNode], summary="Get initiative hierarchy tree")
def get_tree(
    portfolio_id: str | None = Query(None, description="Root at portfolio"),
) -> list[TreeNode]:
    """Get full initiative hierarchy tree (HIER-09)."""
    with get_session() as session:
        portfolios = session.query(Portfolio).all()
        if portfolio_id:
            portfolios = [p for p in portfolios if p.id == portfolio_id]
            if not portfolios:
                raise HTTPException(status_code=404, detail="Portfolio not found")

        def build_program_nodes(program: Program) -> list[TreeNode]:
            projects = session.query(Project).filter_by(program_id=program.id).all()
            return [
                TreeNode(
                    id=p.id,
                    name=p.name,
                    type="project",
                    status=p.prd_status,
                    path_depth=p.path_depth,
                    children=build_sprint_nodes(p),
                )
                for p in projects
            ]

        def build_sprint_nodes(project: Project) -> list[TreeNode]:
            sprints = session.query(Sprint).filter_by(project_id=project.id).all()
            return [
                TreeNode(
                    id=s.id,
                    name=s.name,
                    type="sprint",
                    status=s.status,
                    path_depth=s.path_depth,
                    children=build_task_nodes(s),
                )
                for s in sprints
            ]

        def build_task_nodes(sprint: Sprint) -> list[TreeNode]:
            tasks = session.query(Task).filter_by(sprint_id=sprint.id).all()
            return [
                TreeNode(
                    id=t.id,
                    name=t.name,
                    type="task",
                    status=t.status,
                    path_depth=t.path_depth,
                    children=[],
                )
                for t in tasks
            ]

        def build_program_nodes_for_portfolio(program: Program) -> list[TreeNode]:
            return build_program_nodes(program)

        return [
            TreeNode(
                id=p.id,
                name=p.name,
                type="portfolio",
                status=None,
                path_depth=p.path_depth,
                children=[
                    TreeNode(
                        id=pg.id,
                        name=pg.name,
                        type="program",
                        status=None,
                        path_depth=pg.path_depth,
                        children=build_program_nodes(pg),
                    )
                    for pg in session.query(Program).filter_by(portfolio_id=p.id).all()
                ],
            )
            for p in portfolios
        ]


# Search
@router.get("/search", summary="Search initiatives")
def search_initiatives(
    q: str = Query(..., min_length=1, description="Search query"),
    type: str | None = Query(None, description="Filter by type: portfolio, program, project, sprint, task"),
) -> dict:
    """Search initiatives by name across all levels."""
    results: dict[str, list] = {
        "portfolios": [],
        "programs": [],
        "projects": [],
        "sprints": [],
        "tasks": [],
    }

    with get_session() as session:
        if not type or type == "portfolio":
            results["portfolios"] = [
                {"id": p.id, "name": p.name, "type": "portfolio"}
                for p in session.query(Portfolio).filter(Portfolio.name.like(f"%{q}%")).all()
            ]

        if not type or type == "program":
            results["programs"] = [
                {"id": p.id, "name": p.name, "type": "program", "portfolio_id": p.portfolio_id}
                for p in session.query(Program).filter(Program.name.like(f"%{q}%")).all()
            ]

        if not type or type == "project":
            results["projects"] = [
                {"id": p.id, "name": p.name, "type": "project", "program_id": p.program_id}
                for p in session.query(Project).filter(Project.name.like(f"%{q}%")).all()
            ]

        if not type or type == "sprint":
            results["sprints"] = [
                {"id": s.id, "name": s.name, "type": "sprint", "project_id": s.project_id}
                for s in session.query(Sprint).filter(Sprint.name.like(f"%{q}%")).all()
            ]

        if not type or type == "task":
            results["tasks"] = [
                {"id": t.id, "name": t.name, "type": "task", "sprint_id": t.sprint_id}
                for t in session.query(Task).filter(Task.name.like(f"%{q}%")).all()
            ]

    return results