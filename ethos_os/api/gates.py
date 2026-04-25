"""Gate API - approval gate workflow endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from ethos_os.db import get_session
from ethos_os.models.gate import GateRequest, GateType
from ethos_os.repositories.gate import GateRepository

router = APIRouter(prefix="/gates", tags=["approval gates"])


class GateCreateRequest(BaseModel):
    """Request to create a gate request."""

    gate_type: str = Field(..., description="Gate type: scope | budget")
    entity_id: str = Field(..., description="ID of entity this gate is for")
    entity_type: str = Field(..., description="Type of entity (task, project, etc.)")
    trigger_condition: dict[str, Any] = Field(default_factory=dict, description="What triggered this gate")
    approver: str | None = Field(None, description="Assigned approver user ID")
    timeout_hours: int | None = Field(None, description="Timeout in hours (default: 48h scope, 24h budget)")


class GateDecisionRequest(BaseModel):
    """Request to approve or reject a gate."""

    decided_by: str = Field(..., description="User ID making the decision")
    notes: str | None = Field(None, description="Decision notes")


class GateResponse(BaseModel):
    """Gate request response."""

    id: str
    gate_type: str
    entity_id: str
    entity_type: str
    status: str
    trigger_condition: dict | None
    approver: str | None
    decision_notes: str | None
    decided_by: str | None
    decided_at: str | None
    timeout_hours: int
    created_at: str | None
    age_hours: float

    model_config = ConfigDict(from_attributes=True)


class GateDashboardResponse(BaseModel):
    """Dashboard data for gates."""

    pending_count: int
    pending_by_type: dict[str, int]
    approval_rate_30d: float
    pending_gates: list[GateResponse]


def _gate_to_response(gate: GateRequest) -> GateResponse:
    return GateResponse(
        id=gate.id,
        gate_type=gate.gate_type,
        entity_id=gate.entity_id,
        entity_type=gate.entity_type,
        status=gate.status,
        trigger_condition=gate.trigger_data,
        approver=gate.approver,
        decision_notes=gate.decision_notes,
        decided_by=gate.decided_by,
        decided_at=gate.decided_at.isoformat() if gate.decided_at else None,
        timeout_hours=gate.timeout_hours,
        created_at=gate.created_at.isoformat() if gate.created_at else None,
        age_hours=gate.age_hours,
    )


@router.post("", response_model=GateResponse, status_code=201, summary="Create gate request")
def create_gate(request: GateCreateRequest) -> GateResponse:
    """Create a new gate request (manual trigger or auto-triggered by system)."""
    if request.gate_type not in [GateType.SCOPE.value, GateType.BUDGET.value]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid gate_type: {request.gate_type}. Must be 'scope' or 'budget'."
        )

    with get_session() as session:
        repo = GateRepository(session)
        gate = repo.create(
            gate_type=request.gate_type,
            entity_id=request.entity_id,
            entity_type=request.entity_type,
            trigger_condition=request.trigger_condition,
            approver=request.approver,
            timeout_hours=request.timeout_hours,
        )
        session.commit()
        return _gate_to_response(gate)


@router.get("", response_model=list[GateResponse], summary="List gate requests")
def list_gates(
    status: str | None = Query(None, description="Filter by status: pending, approved, rejected"),
    gate_type: str | None = Query(None, description="Filter by type: scope, budget"),
    entity_id: str | None = Query(None, description="Filter by entity ID"),
    limit: int | None = Query(None, description="Limit results"),
) -> list[GateResponse]:
    """List gate requests with optional filters."""
    with get_session() as session:
        repo = GateRepository(session)
        gates = repo.list(
            status=status,
            gate_type=gate_type,
            entity_id=entity_id,
            limit=limit,
        )
        return [_gate_to_response(g) for g in gates]


@router.get("/pending", response_model=list[GateResponse], summary="List pending gates")
def list_pending_gates(
    gate_type: str | None = Query(None, description="Filter by type: scope, budget"),
) -> list[GateResponse]:
    """List all pending gate requests ordered by age (oldest first) (GATE-08)."""
    with get_session() as session:
        repo = GateRepository(session)
        pending = repo.get_pending()
        if gate_type:
            pending = [g for g in pending if g.gate_type == gate_type]
        return [_gate_to_response(g) for g in pending]


@router.get("/dashboard", response_model=GateDashboardResponse, summary="Get gate dashboard data")
def get_gate_dashboard() -> GateDashboardResponse:
    """Get dashboard data: pending counts, approval rate, aging gates."""
    with get_session() as session:
        repo = GateRepository(session)
        pending = repo.get_pending()
        approval_rate = repo.get_approval_rate(days=30)
        pending_by_type = repo.count_pending_by_type()

        return GateDashboardResponse(
            pending_count=len(pending),
            pending_by_type=pending_by_type,
            approval_rate_30d=approval_rate,
            pending_gates=[_gate_to_response(g) for g in pending],
        )


@router.get("/{gate_id}", response_model=GateResponse, summary="Get gate request")
def get_gate(gate_id: str) -> GateResponse:
    """Get a gate request by ID."""
    with get_session() as session:
        repo = GateRepository(session)
        gate = repo.get(gate_id)
        if not gate:
            raise HTTPException(status_code=404, detail="Gate not found")
        return _gate_to_response(gate)


@router.post("/{gate_id}/approve", response_model=GateResponse, summary="Approve gate")
def approve_gate(gate_id: str, request: GateDecisionRequest) -> GateResponse:
    """Approve a pending gate request (GATE-03). Task unblocks upon approval."""
    with get_session() as session:
        repo = GateRepository(session)
        try:
            gate = repo.approve(
                id=gate_id,
                decided_by=request.decided_by,
                notes=request.notes,
            )
            session.commit()
            return _gate_to_response(gate)
        except KeyError:
            raise HTTPException(status_code=404, detail="Gate not found")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))


@router.post("/{gate_id}/reject", response_model=GateResponse, summary="Reject gate")
def reject_gate(gate_id: str, request: GateDecisionRequest) -> GateResponse:
    """Reject a pending gate request (GATE-03, GATE-05). Task blocked until re-planned."""
    with get_session() as session:
        repo = GateRepository(session)
        try:
            gate = repo.reject(
                id=gate_id,
                decided_by=request.decided_by,
                notes=request.notes,
            )
            session.commit()
            return _gate_to_response(gate)
        except KeyError:
            raise HTTPException(status_code=404, detail="Gate not found")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))


@router.get("/entity/{entity_id}", response_model=list[GateResponse], summary="Get gate history for entity")
def get_entity_gates(entity_id: str) -> list[GateResponse]:
    """Get all gate history for an entity (GATE-06: immutable records)."""
    with get_session() as session:
        repo = GateRepository(session)
        gates = repo.get_all_for_entity(entity_id)
        return [_gate_to_response(g) for g in gates]


@router.get("/entity/{entity_id}/pending", response_model=list[GateResponse], summary="Get pending gates for entity")
def get_entity_pending_gates(entity_id: str) -> list[GateResponse]:
    """Check if entity has pending gates (used before task execution)."""
    with get_session() as session:
        repo = GateRepository(session)
        gates = repo.get_pending_for_entity(entity_id)
        return [_gate_to_response(g) for g in gates]


@router.get("/stats/approval-rate", response_model=dict, summary="Get gate approval rate")
def get_approval_rate(days: int = Query(30, ge=1, le=365)) -> dict:
    """Get gate approval rate for the last N days. Flag 100% rate as gate theater."""
    with get_session() as session:
        repo = GateRepository(session)
        rate = repo.get_approval_rate(days=days)
        return {
            "days": days,
            "approval_rate": rate,
            "theater_warning": rate >= 1.0,
            "theater_message": "100% approval rate detected - gates may be theatrical rather than substantive"
            if rate >= 1.0 else None,
        }