"""Gate dashboard service - data for dashboard display."""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from ethos_os.models.gate import GateStatus, GateType
from ethos_os.repositories.gate import GateRepository


class GateDashboardService:
    """Service for gate dashboard data."""

    def __init__(self, session: Session):
        self.session = session
        self.gate_repo = GateRepository(session)

    def get_pending_gates(self) -> list[dict[str, Any]]:
        """Get pending gates with age calculation."""
        pending = self.gate_repo.get_pending()
        gates = []

        for gate in pending:
            gates.append({
                "id": gate.id,
                "gate_type": gate.gate_type,
                "entity_id": gate.entity_id,
                "entity_type": gate.entity_type,
                "status": gate.status,
                "approver": gate.approver,
                "age_hours": gate.age_hours,
                "timeout_hours": gate.timeout_hours,
                "trigger": gate.trigger_data,
                "created_at": gate.created_at.isoformat() if gate.created_at else None,
            })

        return gates

    def get_summary(self) -> dict[str, Any]:
        """Get gate summary for dashboard."""
        pending = self.gate_repo.get_pending()
        pending_by_type = self.gate_repo.count_pending_by_type()
        approval_rate = self.gate_repo.get_approval_rate()

        # Calculate average decision time
        from sqlalchemy import select
        from ethos_os.models.gate import GateRequest

        stmt = select(GateRequest).where(GateRequest.status != GateStatus.PENDING.value)
        decided = list(self.session.execute(stmt).scalars().all())

        decision_times = []
        for gate in decided:
            if gate.created_at and gate.decided_at:
                delta = gate.decided_at - gate.created_at
                decision_times.append(delta.total_seconds() / 3600)

        avg_decision_hours = (
            sum(decision_times) / len(decision_times) if decision_times else 0
        )

        return {
            "pending_total": len(pending),
            "pending_scope": pending_by_type.get("scope", 0),
            "pending_budget": pending_by_type.get("budget", 0),
            "approval_rate": approval_rate,
            "avg_decision_hours": round(avg_decision_hours, 2),
        }

    def get_gate_metrics(self, days: int = 30) -> dict[str, Any]:
        """Get gate metrics over time period."""
        from sqlalchemy import select
        from ethos_os.models.gate import GateRequest

        cutoff = datetime.now() - timedelta(days=days)
        stmt = select(GateRequest).where(GateRequest.created_at >= cutoff)
        gates = list(self.session.execute(stmt).scalars().all())

        total = len(gates)
        if total == 0:
            return {
                "period_days": days,
                "total": 0,
                "approved": 0,
                "rejected": 0,
                "pending": 0,
                "approval_rate": 0.0,
            }

        approved = sum(1 for g in gates if g.status == GateStatus.APPROVED.value)
        rejected = sum(1 for g in gates if g.status == GateStatus.REJECTED.value)
        pending = sum(1 for g in gates if g.status == GateStatus.PENDING.value)

        return {
            "period_days": days,
            "total": total,
            "approved": approved,
            "rejected": rejected,
            "pending": pending,
            "approval_rate": round(approved / (approved + rejected), 2) if (approved + rejected) > 0 else 0.0,
        }

    def is_gates_aging(self, threshold_hours: float = 24.0) -> bool:
        """Check if any pending gates are approaching timeout."""
        pending = self.gate_repo.get_pending()
        for gate in pending:
            if gate.age_hours >= threshold_hours:
                return True
        return False