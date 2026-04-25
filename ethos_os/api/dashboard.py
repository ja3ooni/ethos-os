"""Dashboard metrics API - budget, performance, agent status summary."""

from fastapi import APIRouter, Query
from pydantic import BaseModel

from ethos_os.db import get_session
from ethos_os.execution.heartbeat import Heartbeat

try:
    from ethos_os.orchestration.budget import AgentSpendingRecord
except ImportError:
    AgentSpendingRecord = None

router = APIRouter(prefix="/dashboard", tags=["dashboard-metrics"])


class BudgetSummary(BaseModel):
    """Budget summary per initiative/project."""

    item_id: str
    item_name: str
    item_type: str
    budget_allocated: float | None
    spent: float
    remaining: float
    pct_used: float


class DashboardMetricsResponse(BaseModel):
    """Dashboard metrics response."""

    total_budget_allocated: float
    total_spent: float
    budget_by_initiative: list[BudgetSummary]
    agent_summary: list[dict]
    pending_gates_count: int


class AgentPerformanceSummary(BaseModel):
    """Agent performance summary."""

    agent_id: str
    agent_name: str
    tasks_completed: int
    tasks_working: int
    avg_response_time_ms: float | None
    total_cost_usd: float
    status: str


@router.get("/metrics", response_model=DashboardMetricsResponse)
def get_dashboard_metrics() -> DashboardMetricsResponse:
    """Get dashboard metrics: budget summary, agent status, pending gates."""
    with get_session() as session:
        from ethos_os.models.project import Project
        from ethos_os.models.program import Program
        from ethos_os.models.portfolio import Portfolio
        from ethos_os.execution.scheduler import AgentRegistry

        projects = session.query(Project).all()
        total_budget = sum(p.budget or 0 for p in projects)

        spending = []
        total_spent = 0.0
        if AgentSpendingRecord is not None:
            try:
                spending = session.query(AgentSpendingRecord).all()
                total_spent = sum(float(r.call_cost_usd) for r in spending)
            except Exception:
                pass

        budget_by_initiative = []
        for p in projects[:10]:
            project_spend = 0.0
            budget_by_initiative.append(
                BudgetSummary(
                    item_id=p.id,
                    item_name=p.name,
                    item_type="project",
                    budget_allocated=float(p.budget) if p.budget else None,
                    spent=project_spend,
                    remaining=float(p.budget - project_spend) if p.budget else 0,
                    pct_used=(project_spend / float(p.budget) * 100) if p.budget else 0,
                )
            )

        registry = AgentRegistry(session)
        agents = registry.get_all()

        agent_summary = []
        for a in agents:
            heartbeats = (
                session.query(Heartbeat)
                .where(Heartbeat.agent_id == a.id)
                .order_by(Heartbeat.timestamp.desc())
                .limit(10)
                .all()
            )
            agent_summary.append(
                {
                    "id": a.id,
                    "name": a.name,
                    "status": a.status,
                    "current_task_id": a.current_task_id,
                    "last_heartbeat": a.last_heartbeat_at.isoformat() if a.last_heartbeat_at else None,
                    "heartbeat_count": len(heartbeats),
                }
            )

        from ethos_os.models.gate import GateRequest
        pending_gates = session.query(GateRequest).filter_by(status="pending").count()

        return DashboardMetricsResponse(
            total_budget_allocated=total_budget,
            total_spent=total_spent,
            budget_by_initiative=budget_by_initiative,
            agent_summary=agent_summary,
            pending_gates_count=pending_gates,
        )


@router.get("/agent-performance", response_model=list[AgentPerformanceSummary])
def get_agent_performance(limit: int = Query(50, ge=1, le=100)) -> list[AgentPerformanceSummary]:
    """Get agent performance metrics (DASH-04)."""
    with get_session() as session:
        from ethos_os.execution.scheduler import AgentRegistry
        from ethos_os.execution.heartbeat import Heartbeat

        registry = AgentRegistry(session)
        agents = registry.get_all()

        results = []
        for a in agents[:limit]:
            heartbeats = (
                session.query(Heartbeat)
                .where(Heartbeat.agent_id == a.id)
                .order_by(Heartbeat.timestamp.desc())
                .limit(100)
                .all()
            )

            completed = sum(1 for h in heartbeats if h.status == "complete")
            working = sum(1 for h in heartbeats if h.status == "working")

            total_cost = 0.0
            if AgentSpendingRecord is not None:
                try:
                    costs = (
                        session.query(AgentSpendingRecord)
                        .where(AgentSpendingRecord.agent_id == a.id)
                        .all()
                    )
                    total_cost = sum(float(c.call_cost_usd) for c in costs)
                except Exception:
                    pass

            results.append(
                AgentPerformanceSummary(
                    agent_id=a.id,
                    agent_name=a.name,
                    tasks_completed=completed,
                    tasks_working=working,
                    avg_response_time_ms=None,
                    total_cost_usd=total_cost,
                    status=a.status,
                )
            )

        return results


@router.get("/budget/initiatives", response_model=list[BudgetSummary])
def get_budget_by_initiative() -> list[BudgetSummary]:
    """Get budget tracking per initiative (DASH-04)."""
    with get_session() as session:
        from ethos_os.models.project import Project
        from ethos_os.models.program import Program
        from ethos_os.models.portfolio import Portfolio

        results = []

        portfolios = session.query(Portfolio).all()
        for p in portfolios:
            results.append(
                BudgetSummary(
                    item_id=p.id,
                    item_name=p.name,
                    item_type="portfolio",
                    budget_allocated=None,
                    spent=0,
                    remaining=0,
                    pct_used=0,
                )
            )

        programs = session.query(Program).all()
        for p in programs:
            results.append(
                BudgetSummary(
                    item_id=p.id,
                    item_name=p.name,
                    item_type="program",
                    budget_allocated=None,
                    spent=0,
                    remaining=0,
                    pct_used=0,
                )
            )

        projects = session.query(Project).all()
        spending = session.query(AgentSpendingRecord).all()

        for p in projects:
            proj_spend = 0.0
            results.append(
                BudgetSummary(
                    item_id=p.id,
                    item_name=p.name,
                    item_type="project",
                    budget_allocated=float(p.budget) if p.budget else None,
                    spent=proj_spend,
                    remaining=float(p.budget - proj_spend) if p.budget else 0,
                    pct_used=(proj_spend / float(p.budget) * 100) if p.budget else 0,
                )
            )

        return results