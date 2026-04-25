"""Gate repository - CRUD and workflow for approval gates."""

import json
from datetime import datetime, timedelta
from typing import Any, List

from sqlalchemy import select
from sqlalchemy.orm import Session

from ethos_os.models.gate import GateRequest, GateStatus, GateType


class GateRepository:
    """Repository for GateRequest operations."""

    model_class = GateRequest

    def __init__(self, session: Session):
        self.session = session

    def _commit(self) -> None:
        self.session.commit()

    def _rollback(self) -> None:
        self.session.rollback()

    def _refresh(self, instance: GateRequest) -> None:
        self.session.refresh(instance)

    def create(
        self,
        gate_type: str,
        entity_id: str,
        entity_type: str,
        trigger_condition: dict[str, Any],
        approver: str | None = None,
        timeout_hours: int | None = None,
    ) -> GateRequest:
        """Create a new gate request."""
        # Set default timeout based on gate type
        if timeout_hours is None:
            timeout_hours = 48 if gate_type == GateType.SCOPE.value else 24

        data = {
            "gate_type": gate_type,
            "entity_id": entity_id,
            "entity_type": entity_type,
            "status": GateStatus.PENDING.value,
            "trigger_condition": json.dumps(trigger_condition),
            "approver": approver,
            "timeout_hours": timeout_hours,
        }
        instance = GateRequest(**data)
        self.session.add(instance)
        self.session.flush()
        self._refresh(instance)
        return instance

    def get(self, id: str) -> GateRequest | None:
        """Get a gate request by ID."""
        return self.session.get(GateRequest, id)

    def get_or_404(self, id: str) -> GateRequest:
        """Get a gate request by ID or raise KeyError."""
        instance = self.session.get(GateRequest, id)
        if instance is None:
            raise KeyError(f"GateRequest not found: {id}")
        return instance

    def get_pending(self) -> List[GateRequest]:
        """List all pending gate requests ordered by age (oldest first)."""
        stmt = (
            select(GateRequest)
            .where(GateRequest.status == GateStatus.PENDING.value)
            .order_by(GateRequest.created_at)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_pending_for_entity(self, entity_id: str) -> List[GateRequest]:
        """Get pending gates for a specific entity."""
        stmt = (
            select(GateRequest)
            .where(GateRequest.entity_id == entity_id)
            .where(GateRequest.status == GateStatus.PENDING.value)
            .order_by(GateRequest.created_at)
        )
        return list(self.session.execute(stmt).scalars().all())

    def has_pending_gate(self, entity_id: str) -> bool:
        """Check if entity has any pending gate."""
        stmt = select(GateRequest).where(GateRequest.entity_id == entity_id).where(
            GateRequest.status == GateStatus.PENDING.value
        )
        return self.session.execute(stmt).first() is not None

    def get_all_for_entity(self, entity_id: str) -> List[GateRequest]:
        """Get all gates for an entity (history)."""
        stmt = select(GateRequest).where(GateRequest.entity_id == entity_id).order_by(
            GateRequest.created_at.desc()
        )
        return list(self.session.execute(stmt).scalars().all())

    def approve(
        self, id: str, decided_by: str, notes: str | None = None
    ) -> GateRequest:
        """Approve a gate request."""
        gate = self.get_or_404(id)
        if gate.status != GateStatus.PENDING.value:
            raise ValueError(f"Gate {id} is not pending (status: {gate.status})")

        gate.status = GateStatus.APPROVED.value
        gate.decided_by = decided_by
        gate.decision_notes = notes
        gate.decided_at = datetime.now(gate.created_at.tzinfo)
        self.session.flush()
        self._refresh(gate)
        return gate

    def reject(
        self, id: str, decided_by: str, notes: str | None = None
    ) -> GateRequest:
        """Reject a gate request."""
        gate = self.get_or_404(id)
        if gate.status != GateStatus.PENDING.value:
            raise ValueError(f"Gate {id} is not pending (status: {gate.status})")

        gate.status = GateStatus.REJECTED.value
        gate.decided_by = decided_by
        gate.decision_notes = notes
        gate.decided_at = datetime.now(gate.created_at.tzinfo)
        self.session.flush()
        self._refresh(gate)
        return gate

    def list(
        self,
        status: str | None = None,
        gate_type: str | None = None,
        entity_id: str | None = None,
        limit: int | None = None,
    ) -> List[GateRequest]:
        """List gates with optional filters."""
        stmt = select(GateRequest)

        if status:
            stmt = stmt.where(GateRequest.status == status)
        if gate_type:
            stmt = stmt.where(GateRequest.gate_type == gate_type)
        if entity_id:
            stmt = stmt.where(GateRequest.entity_id == entity_id)

        stmt = stmt.order_by(GateRequest.created_at.desc())

        if limit:
            stmt = stmt.limit(limit)

        return list(self.session.execute(stmt).scalars().all())

    def count_pending_by_type(self) -> dict[str, int]:
        """Count pending gates by type."""
        pending = self.get_pending()
        return {
            "scope": sum(1 for g in pending if g.gate_type == GateType.SCOPE.value),
            "budget": sum(1 for g in pending if g.gate_type == GateType.BUDGET.value),
        }

    def get_approval_rate(self, days: int = 30) -> float:
        """Calculate gate approval rate for recent gates."""
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=days)
        stmt = select(GateRequest).where(GateRequest.created_at >= cutoff)
        gates = list(self.session.execute(stmt).scalars().all())

        if not gates:
            return 0.0

        decided = [g for g in gates if g.status != GateStatus.PENDING.value]
        if not decided:
            return 0.0

        approved = sum(1 for g in decided if g.status == GateStatus.APPROVED.value)
        return approved / len(decided)