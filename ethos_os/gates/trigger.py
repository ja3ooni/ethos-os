"""Gate trigger service - auto-create gates when thresholds exceeded."""

from sqlalchemy.orm import Session

from ethos_os.models.gate import GateType
from ethos_os.repositories.gate import GateRepository


# Thresholds as per requirements
SCOPE_THRESHOLD = 1.25  # +25% effort variance triggers scope gate
BUDGET_THRESHOLD = 1.20  # +20% cost variance triggers budget gate


class GateTriggerService:
    """Service for evaluating and triggering gates."""

    def __init__(self, session: Session):
        self.session = session
        self.gate_repo = GateRepository(session)

    def check_scope_gate(
        self,
        task_id: str,
        original_estimate: float,
        actual_effort: float,
        approver: str | None = None,
    ) -> tuple[bool, str | None]:
        """Check if scope gate should be triggered.
        
        Returns (triggered, gate_id):
        - triggered: True if threshold exceeded and no pending gate exists
        - gate_id: ID of created gate or None
        """
        # Check if threshold exceeded
        if actual_effort < original_estimate * SCOPE_THRESHOLD:
            return False, None

        # Check if pending gate already exists
        if self.gate_repo.has_pending_gate(task_id):
            return False, None

        # Create gate request
        trigger_condition = {
            "reason": "scope_variance",
            "original_estimate": original_estimate,
            "actual_effort": actual_effort,
            "variance_pct": ((actual_effort / original_estimate) - 1) * 100,
            "threshold_pct": (SCOPE_THRESHOLD - 1) * 100,
        }

        gate = self.gate_repo.create(
            gate_type=GateType.SCOPE.value,
            entity_id=task_id,
            entity_type="task",
            trigger_condition=trigger_condition,
            approver=approver,
        )

        return True, gate.id

    def check_budget_gate(
        self,
        entity_id: str,
        entity_type: str,
        estimated_cost: float,
        actual_cost: float,
        approver: str | None = None,
    ) -> tuple[bool, str | None]:
        """Check if budget gate should be triggered.
        
        Returns (triggered, gate_id):
        - triggered: True if threshold exceeded and no pending gate exists
        - gate_id: ID of created gate or None
        """
        # Check if threshold exceeded
        if actual_cost < estimated_cost * BUDGET_THRESHOLD:
            return False, None

        # Check if pending gate already exists
        if self.gate_repo.has_pending_gate(entity_id):
            return False, None

        # Create gate request
        trigger_condition = {
            "reason": "budget_variance",
            "estimated_cost": estimated_cost,
            "actual_cost": actual_cost,
            "variance_pct": ((actual_cost / estimated_cost) - 1) * 100,
            "threshold_pct": (BUDGET_THRESHOLD - 1) * 100,
        }

        gate = self.gate_repo.create(
            gate_type=GateType.BUDGET.value,
            entity_id=entity_id,
            entity_type=entity_type,
            trigger_condition=trigger_condition,
            approver=approver,
            timeout_hours=24,  # Budget gates have shorter timeout
        )

        return True, gate.id

    def can_proceed(self, entity_id: str) -> bool:
        """Check if entity can proceed (no pending gates)."""
        return not self.gate_repo.has_pending_gate(entity_id)