"""Orchestration API endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ethos_os.db import get_session
from ethos_os.orchestration import (
    get_task_router,
    get_task_queue,
    get_status_tracker,
    get_budget_enforcer,
    get_failure_detector,
)

router = APIRouter(prefix="/orchestration", tags=["orchestration"])


@router.post("/route/{task_id}")
def route_task(
    task_id: str,
    capabilities: list[str] | None = None,
    role: str | None = None,
    division: str | None = None,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Route task to best capable agent."""
    router = get_task_router(session)
    agent_id = router.assign_best_agent(
        task_id,
        required_capabilities=capabilities,
        preferred_role=role,
        preferred_division=division,
    )

    if not agent_id:
        raise HTTPException(status_code=404, detail="No capable agent found")

    return {"task_id": task_id, "agent_id": agent_id}


@router.get("/tasks/eligible/{agent_id}")
def get_eligible_tasks(
    agent_id: str,
    limit: int = 10,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Get tasks eligible for agent."""
    queue = get_task_queue(session)
    tasks = queue.get_eligible_tasks(agent_id, limit)
    return {"agent_id": agent_id, "tasks": tasks}


@router.post("/tasks/{task_id}/checkout")
def checkout_task(
    task_id: str,
    agent_id: str,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Checkout task for agent (atomic lock)."""
    queue = get_task_queue(session)
    success = queue.checkout(task_id, agent_id)

    if not success:
        raise HTTPException(status_code=409, detail="Task already claimed")

    return {"task_id": task_id, "agent_id": agent_id, "status": "checked_out"}


@router.post("/tasks/{task_id}/release")
def release_task(
    task_id: str,
    agent_id: str,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Release task lock."""
    queue = get_task_queue(session)
    success = queue.release(task_id, agent_id)

    if not success:
        raise HTTPException(status_code=403, detail="Not task owner")

    return {"task_id": task_id, "status": "released"}


@router.post("/tasks/{task_id}/complete")
def complete_task(
    task_id: str,
    agent_id: str,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Mark task as complete."""
    queue = get_task_queue(session)
    success = queue.complete(task_id, agent_id)

    if not success:
        raise HTTPException(status_code=403, detail="Not task owner")

    return {"task_id": task_id, "status": "complete"}


@router.post("/agents/{agent_id}/status")
def transition_status(
    agent_id: str,
    status: str,
    task_id: str | None = None,
    reason: str | None = None,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Transition agent status."""
    tracker = get_status_tracker(session)
    success = tracker.transition(agent_id, task_id, status, reason)

    if not success:
        raise HTTPException(status_code=400, detail="Invalid status transition")

    return {"agent_id": agent_id, "status": status}


@router.get("/agents/{agent_id}/status")
def get_agent_status(
    agent_id: str,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Get agent current status."""
    tracker = get_status_tracker(session)
    status = tracker.get_current_status(agent_id)
    return {"agent_id": agent_id, "status": status}


@router.get("/agents/{agent_id}/budget")
def get_agent_budget(
    agent_id: str,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Get agent budget status."""
    enforcer = get_budget_enforcer(session)
    budget = enforcer.get_remaining_budget(agent_id)
    return {"agent_id": agent_id, **budget}


@router.get("/agents/{agent_id}/failures")
def get_agent_failures(
    agent_id: str,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Get agent failures."""
    detector = get_failure_detector(session)
    failures = detector.get_unresolved_failures(agent_id)
    return {"agent_id": agent_id, "failures": failures}


@router.post("/agents/{agent_id}/reassign")
def reassign_tasks(
    agent_id: str,
    new_agent_id: str | None = None,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Reassign tasks from failed agent."""
    detector = get_failure_detector(session)
    tasks = detector.reassign_tasks(agent_id, new_agent_id)

    return {"failed_agent_id": agent_id, "new_agent_id": new_agent_id, "tasks": tasks}