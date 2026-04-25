"""API integration tests for gate endpoints."""

import pytest
from fastapi.testclient import TestClient

from ethos_os.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    from ethos_os.db import Base, get_engine

    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


class TestGateAPI:
    def test_create_scope_gate(self):
        response = client.post(
            "/gates",
            json={
                "gate_type": "scope",
                "entity_id": "task-001",
                "entity_type": "task",
                "trigger_condition": {"type": "effort_variance", "threshold": 1.25, "actual": 1.3},
                "approver": "user-001",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["gate_type"] == "scope"
        assert data["entity_id"] == "task-001"
        assert data["status"] == "pending"
        assert data["timeout_hours"] == 48

    def test_create_budget_gate(self):
        response = client.post(
            "/gates",
            json={
                "gate_type": "budget",
                "entity_id": "task-002",
                "entity_type": "task",
                "trigger_condition": {"type": "cost_variance", "threshold": 1.2, "actual": 1.25},
            },
        )
        assert response.status_code == 201
        assert response.json()["gate_type"] == "budget"
        assert response.json()["timeout_hours"] == 24

    def test_create_gate_invalid_type(self):
        response = client.post(
            "/gates",
            json={
                "gate_type": "invalid",
                "entity_id": "task-001",
                "entity_type": "task",
            },
        )
        assert response.status_code == 400

    def test_list_gates(self):
        client.post(
            "/gates",
            json={"gate_type": "scope", "entity_id": "task-001", "entity_type": "task"},
        )
        client.post(
            "/gates",
            json={"gate_type": "budget", "entity_id": "task-002", "entity_type": "task"},
        )
        response = client.get("/gates")
        assert response.status_code == 200
        assert len(response.json()) >= 2

    def test_list_pending_gates_ordered_by_age(self):
        client.post(
            "/gates",
            json={"gate_type": "scope", "entity_id": "task-001", "entity_type": "task"},
        )
        client.post(
            "/gates",
            json={"gate_type": "budget", "entity_id": "task-002", "entity_type": "task"},
        )
        response = client.get("/gates/pending")
        assert response.status_code == 200
        gates = response.json()
        assert all(g["status"] == "pending" for g in gates)

    def test_get_gate_dashboard(self):
        client.post(
            "/gates",
            json={"gate_type": "scope", "entity_id": "task-001", "entity_type": "task"},
        )
        response = client.get("/gates/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "pending_count" in data
        assert "pending_by_type" in data
        assert "approval_rate_30d" in data
        assert "pending_gates" in data

    def test_approve_gate(self):
        gate_resp = client.post(
            "/gates",
            json={
                "gate_type": "scope",
                "entity_id": "task-001",
                "entity_type": "task",
            },
        )
        gate_id = gate_resp.json()["id"]

        response = client.post(
            f"/gates/{gate_id}/approve",
            json={"decided_by": "manager-001", "notes": "LGTM"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"
        assert data["decided_by"] == "manager-001"
        assert data["decision_notes"] == "LGTM"
        assert data["decided_at"] is not None

    def test_reject_gate(self):
        gate_resp = client.post(
            "/gates",
            json={
                "gate_type": "scope",
                "entity_id": "task-001",
                "entity_type": "task",
            },
        )
        gate_id = gate_resp.json()["id"]

        response = client.post(
            f"/gates/{gate_id}/reject",
            json={
                "decided_by": "manager-001",
                "notes": "Scope too aggressive, need to re-plan",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"
        assert data["decision_notes"] == "Scope too aggressive, need to re-plan"

    def test_cannot_approve_non_pending_gate(self):
        gate_resp = client.post(
            "/gates",
            json={"gate_type": "scope", "entity_id": "task-001", "entity_type": "task"},
        )
        gate_id = gate_resp.json()["id"]
        client.post(f"/gates/{gate_id}/approve", json={"decided_by": "mgr"})

        response = client.post(f"/gates/{gate_id}/approve", json={"decided_by": "mgr"})
        assert response.status_code == 400
        assert "not pending" in response.json()["detail"]

    def test_get_gate_not_found(self):
        response = client.get("/gates/nonexistent-id")
        assert response.status_code == 404

    def test_approve_gate_not_found(self):
        response = client.post(
            "/gates/nonexistent-id/approve",
            json={"decided_by": "mgr"},
        )
        assert response.status_code == 404

    def test_entity_gate_history(self):
        client.post(
            "/gates",
            json={"gate_type": "scope", "entity_id": "task-001", "entity_type": "task"},
        )
        client.post(
            "/gates",
            json={"gate_type": "scope", "entity_id": "task-001", "entity_type": "task"},
        )

        gate_resp = client.get("/gates?entity_id=task-001")
        first_gate_id = gate_resp.json()[0]["id"]
        client.post(
            f"/gates/{first_gate_id}/approve",
            json={"decided_by": "mgr"},
        )

        response = client.get("/gates/entity/task-001")
        assert response.status_code == 200
        history = response.json()
        assert len(history) == 2

    def test_entity_pending_gates(self):
        gate_resp = client.post(
            "/gates",
            json={"gate_type": "scope", "entity_id": "task-001", "entity_type": "task"},
        )
        gate_id = gate_resp.json()["id"]

        response = client.get("/gates/entity/task-001/pending")
        assert response.status_code == 200
        assert len(response.json()) == 1

        client.post(f"/gates/{gate_id}/approve", json={"decided_by": "mgr"})

        response = client.get("/gates/entity/task-001/pending")
        assert len(response.json()) == 0

    def test_approval_rate_endpoint(self):
        client.post(
            "/gates",
            json={"gate_type": "scope", "entity_id": "task-001", "entity_type": "task"},
        )
        response = client.get("/gates/stats/approval-rate")
        assert response.status_code == 200
        data = response.json()
        assert "approval_rate" in data
        assert "days" in data
        assert data["days"] == 30

    def test_filter_gates_by_type(self):
        client.post(
            "/gates",
            json={"gate_type": "scope", "entity_id": "task-001", "entity_type": "task"},
        )
        client.post(
            "/gates",
            json={"gate_type": "budget", "entity_id": "task-002", "entity_type": "task"},
        )
        response = client.get("/gates?gate_type=scope")
        assert response.status_code == 200
        gates = response.json()
        assert all(g["gate_type"] == "scope" for g in gates)

    def test_gate_timeout_calculation(self):
        response = client.post(
            "/gates",
            json={
                "gate_type": "scope",
                "entity_id": "task-001",
                "entity_type": "task",
                "timeout_hours": 72,
            },
        )
        assert response.json()["timeout_hours"] == 72

    def test_gate_age_calculation(self):
        gate_resp = client.post(
            "/gates",
            json={"gate_type": "scope", "entity_id": "task-001", "entity_type": "task"},
        )
        assert gate_resp.json()["age_hours"] >= 0