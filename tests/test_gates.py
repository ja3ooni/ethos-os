"""Integration tests for Phase 2 - gates and audit."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ethos_os.db import Base
from ethos_os.models import GateRequest, GateStatus, GateType
from ethos_os.models import AuditLog, AuditEventType
from ethos_os.models.task import Task, TaskStatus
from ethos_os.models.sprint import Sprint, SprintStatus
from ethos_os.models.project import Project, ProjectStatus
from ethos_os.repositories.gate import GateRepository
from ethos_os.repositories.audit import AuditRepository
from ethos_os.gates.trigger import GateTriggerService, SCOPE_THRESHOLD, BUDGET_THRESHOLD


@pytest.fixture
def session():
    """Create in-memory SQLite session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestGateRepository:
    """Tests for GateRepository."""

    def test_create_scope_gate(self, session):
        """Gate can be created with scope type."""
        gate_repo = GateRepository(session)

        gate = gate_repo.create(
            gate_type=GateType.SCOPE.value,
            entity_id="task-123",
            entity_type="task",
            trigger_condition={"original": 10, "actual": 15},
            approver="approver-1",
        )

        assert gate.id is not None
        assert gate.gate_type == "scope"
        assert gate.entity_id == "task-123"
        assert gate.status == GateStatus.PENDING.value

    def test_create_budget_gate(self, session):
        """Gate can be created with budget type."""
        gate_repo = GateRepository(session)

        gate = gate_repo.create(
            gate_type=GateType.BUDGET.value,
            entity_id="project-456",
            entity_type="project",
            trigger_condition={"estimated": 1000, "actual": 1500},
            approver="approver-1",
            timeout_hours=24,
        )

        assert gate.gate_type == "budget"
        assert gate.timeout_hours == 24

    def test_get_pending_gates(self, session):
        """Pending gates can be listed."""
        gate_repo = GateRepository(session)

        gate_repo.create(
            gate_type=GateType.SCOPE.value,
            entity_id="task-1",
            entity_type="task",
            trigger_condition={},
        )
        gate_repo.create(
            gate_type=GateType.BUDGET.value,
            entity_id="task-2",
            entity_type="task",
            trigger_condition={},
        )

        pending = gate_repo.get_pending()
        assert len(pending) == 2

    def test_approve_gate(self, session):
        """Gate can be approved."""
        gate_repo = GateRepository(session)

        gate = gate_repo.create(
            gate_type=GateType.SCOPE.value,
            entity_id="task-1",
            entity_type="task",
            trigger_condition={},
        )

        approved = gate_repo.approve(gate.id, decided_by="admin-1", notes="Approved")

        assert approved.status == GateStatus.APPROVED.value
        assert approved.decided_by == "admin-1"
        assert approved.decided_at is not None

    def test_reject_gate(self, session):
        """Gate can be rejected."""
        gate_repo = GateRepository(session)

        gate = gate_repo.create(
            gate_type=GateType.SCOPE.value,
            entity_id="task-1",
            entity_type="task",
            trigger_condition={},
        )

        rejected = gate_repo.reject(gate.id, decided_by="admin-1", notes="Too much variance")

        assert rejected.status == GateStatus.REJECTED.value
        assert rejected.decided_by == "admin-1"


class TestGateTrigger:
    """Tests for GateTriggerService."""

    def test_scope_gate_triggers_at_25_percent(self, session):
        """Scope gate triggers at exactly 25% variance."""
        service = GateTriggerService(session)

        triggered, gate_id = service.check_scope_gate(
            task_id="task-1",
            original_estimate=10.0,
            actual_effort=12.5,  # Exactly 25%
            approver="approver-1",
        )

        assert triggered is True
        assert gate_id is not None

    def test_scope_gate_triggers_above_25_percent(self, session):
        """Scope gate triggers above 25% variance."""
        service = GateTriggerService(session)

        triggered, gate_id = service.check_scope_gate(
            task_id="task-1",
            original_estimate=10.0,
            actual_effort=15.0,  # 50% variance
            approver="approver-1",
        )

        assert triggered is True

    def test_scope_gate_does_not_trigger_below_25(self, session):
        """Scope gate does NOT trigger below 25% variance."""
        service = GateTriggerService(session)

        triggered, gate_id = service.check_scope_gate(
            task_id="task-1",
            original_estimate=10.0,
            actual_effort=12.0,  # 20% variance - below threshold
            approver="approver-1",
        )

        assert triggered is False
        assert gate_id is None

    def test_budget_gate_triggers_at_20_percent(self, session):
        """Budget gate triggers at 20% variance."""
        service = GateTriggerService(session)

        triggered, gate_id = service.check_budget_gate(
            entity_id="project-1",
            entity_type="project",
            estimated_cost=1000.0,
            actual_cost=1200.0,  # Exactly 20%
        )

        assert triggered is True

    def test_can_proceed_with_approved_gate(self, session):
        """Entity can proceed after gate approved."""
        service = GateTriggerService(session)
        gate_repo = GateRepository(session)

        gate = gate_repo.create(
            gate_type=GateType.SCOPE.value,
            entity_id="task-1",
            entity_type="task",
            trigger_condition={},
        )

        gate_repo.approve(gate.id, decided_by="admin-1")

        assert service.can_proceed("task-1") is True

    def test_cannot_proceed_with_pending_gate(self, session):
        """Entity blocked while gate pending."""
        service = GateTriggerService(session)

        gate_repo = GateRepository(session)
        gate_repo.create(
            gate_type=GateType.SCOPE.value,
            entity_id="task-1",
            entity_type="task",
            trigger_condition={},
        )

        assert service.can_proceed("task-1") is False


class TestAuditRepository:
    """Tests for AuditRepository."""

    def test_create_audit_entry(self, session):
        """Audit entry can be created."""
        audit_repo = AuditRepository(session)

        entry = audit_repo.create(
            event_type=AuditEventType.HEARTBEAT.value,
            entity_id="agent-1",
            entity_type="agent",
            payload={"status": "working", "task_id": "task-1"},
        )

        assert entry.id is not None
        assert entry.event_type == "heartbeat"
        assert entry.previous_hash is None  # First record

    def test_hash_chain_integrity(self, session):
        """Hash chain is maintained across records."""
        audit_repo = AuditRepository(session)

        entry1 = audit_repo.create(
            event_type=AuditEventType.HEARTBEAT.value,
            entity_id="agent-1",
            entity_type="agent",
            payload={"status": "working"},
        )

        entry2 = audit_repo.create(
            event_type=AuditEventType.GATE_DECISION.value,
            entity_id="gate-1",
            entity_type="gate_request",
            payload={"decision": "approved"},
        )

        assert entry2.previous_hash == entry1.hash
        assert entry2.hash != entry1.hash

    def test_verify_integrity(self, session):
        """Integrity verification passes for valid chain."""
        audit_repo = AuditRepository(session)

        audit_repo.create(
            event_type=AuditEventType.HEARTBEAT.value,
            entity_id="agent-1",
            entity_type="agent",
            payload={"status": "working"},
        )
        audit_repo.create(
            event_type=AuditEventType.GATE_DECISION.value,
            entity_id="gate-1",
            entity_type="gate_request",
            payload={"decision": "approved"},
        )

        is_valid, failed = audit_repo.verify_integrity()
        assert is_valid is True
        assert failed is None

    def test_query_by_entity(self, session):
        """Audit entries can be queried by entity."""
        audit_repo = AuditRepository(session)

        audit_repo.create(
            event_type=AuditEventType.HEARTBEAT.value,
            entity_id="agent-1",
            entity_type="agent",
            payload={"status": "working"},
        )
        audit_repo.create(
            event_type=AuditEventType.HEARTBEAT.value,
            entity_id="agent-1",
            entity_type="agent",
            payload={"status": "idle"},
        )

        entries = audit_repo.list(entity_id="agent-1")
        assert len(entries) == 2


class TestGateApprovalRate:
    """Tests for gate approval rate metrics."""

    def test_approval_rate_calculation(self, session):
        """Approval rate is calculated correctly."""
        gate_repo = GateRepository(session)

        g1 = gate_repo.create(
            gate_type=GateType.SCOPE.value,
            entity_id="task-1",
            entity_type="task",
            trigger_condition={},
        )
        g2 = gate_repo.create(
            gate_type=GateType.SCOPE.value,
            entity_id="task-2",
            entity_type="task",
            trigger_condition={},
        )

        gate_repo.approve(g1.id, decided_by="admin-1")
        gate_repo.approve(g2.id, decided_by="admin-1")

        rate = gate_repo.get_approval_rate()
        assert rate == 1.0

    def test_pending_gates_not_included_in_rate(self, session):
        """Pending gates don't affect approval rate."""
        gate_repo = GateRepository(session)

        gate_repo.create(
            gate_type=GateType.SCOPE.value,
            entity_id="task-1",
            entity_type="task",
            trigger_condition={},
        )

        rate = gate_repo.get_approval_rate()
        assert rate == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])