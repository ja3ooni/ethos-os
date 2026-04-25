"""API integration tests for hierarchy endpoints."""

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


class TestHierarchyAPI:
    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ethos-os"

    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "EthosOS API"
        assert data["version"] == "0.1.0"

    def test_create_portfolio(self):
        response = client.post(
            "/hierarchy/portfolios",
            json={"name": "Tech Portfolio", "strategic_intent": "Transform operations"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Tech Portfolio"
        assert data["strategic_intent"] == "Transform operations"
        assert data["path_depth"] == 1
        assert "id" in data

    def test_list_portfolios(self):
        client.post("/hierarchy/portfolios", json={"name": "Portfolio 1"})
        client.post("/hierarchy/portfolios", json={"name": "Portfolio 2"})
        response = client.get("/hierarchy/portfolios")
        assert response.status_code == 200
        assert len(response.json()) >= 2

    def test_create_program_requires_portfolio(self):
        response = client.post(
            "/hierarchy/programs",
            json={"name": "Test Program", "portfolio_id": "nonexistent"},
        )
        assert response.status_code == 400

    def test_create_program_success(self):
        pf_resp = client.post("/hierarchy/portfolios", json={"name": "Test Portfolio"})
        portfolio_id = pf_resp.json()["id"]

        response = client.post(
            "/hierarchy/programs",
            json={"name": "Test Program", "portfolio_id": portfolio_id},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Program"
        assert data["portfolio_id"] == portfolio_id
        assert data["path_depth"] == 2

    def test_create_project_requires_program(self):
        response = client.post(
            "/hierarchy/projects",
            json={"name": "Test Project", "program_id": "nonexistent"},
        )
        assert response.status_code == 400

    def test_project_prd_status_workflow(self):
        pf_resp = client.post("/hierarchy/portfolios", json={"name": "Portfolio"})
        pg_resp = client.post(
            "/hierarchy/programs",
            json={"name": "Program", "portfolio_id": pf_resp.json()["id"]},
        )
        response = client.post(
            "/hierarchy/projects",
            json={"name": "Test Project", "program_id": pg_resp.json()["id"]},
        )
        assert response.status_code == 201
        assert response.json()["prd_status"] == "draft"

    def test_sprint_requires_approved_project(self):
        pf_resp = client.post("/hierarchy/portfolios", json={"name": "Portfolio"})
        pg_resp = client.post(
            "/hierarchy/programs",
            json={"name": "Program", "portfolio_id": pf_resp.json()["id"]},
        )
        pr_resp = client.post(
            "/hierarchy/projects",
            json={"name": "Project", "program_id": pg_resp.json()["id"]},
        )

        response = client.post(
            "/hierarchy/sprints",
            json={"name": "Sprint 1", "project_id": pr_resp.json()["id"]},
        )
        assert response.status_code == 400
        assert "approved" in response.json()["detail"]

    def test_create_sprint_after_approval(self):
        pf_resp = client.post("/hierarchy/portfolios", json={"name": "Portfolio"})
        pg_resp = client.post(
            "/hierarchy/programs",
            json={"name": "Program", "portfolio_id": pf_resp.json()["id"]},
        )
        pr_resp = client.post(
            "/hierarchy/projects",
            json={"name": "Project", "program_id": pg_resp.json()["id"]},
        )
        project_id = pr_resp.json()["id"]

        client.patch(f"/hierarchy/projects/{project_id}", json={"prd_status": "approved"})
        response = client.post(
            "/hierarchy/sprints",
            json={"name": "Sprint 1", "project_id": project_id},
        )
        assert response.status_code == 201
        assert response.json()["status"] == "planning"

    def test_task_requires_prd_scope_item(self):
        pf_resp = client.post("/hierarchy/portfolios", json={"name": "Portfolio"})
        pg_resp = client.post(
            "/hierarchy/programs",
            json={"name": "Program", "portfolio_id": pf_resp.json()["id"]},
        )
        pr_resp = client.post(
            "/hierarchy/projects",
            json={"name": "Project", "program_id": pg_resp.json()["id"]},
        )
        project_id = pr_resp.json()["id"]
        client.patch(f"/hierarchy/projects/{project_id}", json={"prd_status": "approved"})

        sp_resp = client.post(
            "/hierarchy/sprints",
            json={"name": "Sprint 1", "project_id": project_id},
        )
        sprint_id = sp_resp.json()["id"]

        response = client.post(
            "/hierarchy/tasks",
            json={"name": "Task 1", "sprint_id": sprint_id, "prd_scope_item_id": ""},
        )
        assert response.status_code == 400
        assert "prd_scope_item_id" in response.json()["detail"]

    def test_create_task_success(self):
        pf_resp = client.post("/hierarchy/portfolios", json={"name": "Portfolio"})
        pg_resp = client.post(
            "/hierarchy/programs",
            json={"name": "Program", "portfolio_id": pf_resp.json()["id"]},
        )
        pr_resp = client.post(
            "/hierarchy/projects",
            json={"name": "Project", "program_id": pg_resp.json()["id"]},
        )
        project_id = pr_resp.json()["id"]
        client.patch(f"/hierarchy/projects/{project_id}", json={"prd_status": "approved"})

        sp_resp = client.post(
            "/hierarchy/sprints",
            json={"name": "Sprint 1", "project_id": project_id},
        )
        sprint_id = sp_resp.json()["id"]

        response = client.post(
            "/hierarchy/tasks",
            json={
                "name": "Implement feature",
                "sprint_id": sprint_id,
                "prd_scope_item_id": "prd-scope-001",
                "effort_estimate_hours": 8.0,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Implement feature"
        assert data["prd_scope_item_id"] == "prd-scope-001"
        assert data["status"] == "todo"

    def test_lineage_query_task_to_portfolio(self):
        pf_resp = client.post("/hierarchy/portfolios", json={"name": "Portfolio"})
        pg_resp = client.post(
            "/hierarchy/programs",
            json={"name": "Program", "portfolio_id": pf_resp.json()["id"]},
        )
        pr_resp = client.post(
            "/hierarchy/projects",
            json={"name": "Project", "program_id": pg_resp.json()["id"]},
        )
        project_id = pr_resp.json()["id"]
        client.patch(f"/hierarchy/projects/{project_id}", json={"prd_status": "approved"})

        sp_resp = client.post(
            "/hierarchy/sprints",
            json={"name": "Sprint 1", "project_id": project_id},
        )
        sprint_id = sp_resp.json()["id"]

        tk_resp = client.post(
            "/hierarchy/tasks",
            json={"name": "Task", "sprint_id": sprint_id, "prd_scope_item_id": "ref-001"},
        )
        task_id = tk_resp.json()["id"]

        response = client.get(f"/hierarchy/tasks/{task_id}/lineage")
        assert response.status_code == 200
        lineage = response.json()
        assert lineage["portfolio"] is not None
        assert lineage["portfolio"]["name"] == "Portfolio"
        assert lineage["task"]["id"] == task_id

    def test_search_initiatives(self):
        client.post("/hierarchy/portfolios", json={"name": "Alpha Portfolio"})
        client.post("/hierarchy/portfolios", json={"name": "Beta Portfolio"})
        response = client.get("/hierarchy/search?q=Alpha")
        assert response.status_code == 200
        results = response.json()
        assert len(results["portfolios"]) >= 1
        assert any(p["name"] == "Alpha Portfolio" for p in results["portfolios"])

    def test_full_hierarchy_tree(self):
        pf_resp = client.post("/hierarchy/portfolios", json={"name": "Portfolio"})
        pg_resp = client.post(
            "/hierarchy/programs",
            json={"name": "Program", "portfolio_id": pf_resp.json()["id"]},
        )
        pr_resp = client.post(
            "/hierarchy/projects",
            json={"name": "Project", "program_id": pg_resp.json()["id"]},
        )
        project_id = pr_resp.json()["id"]
        client.patch(f"/hierarchy/projects/{project_id}", json={"prd_status": "approved"})

        sp_resp = client.post(
            "/hierarchy/sprints",
            json={"name": "Sprint 1", "project_id": project_id},
        )
        sprint_id = sp_resp.json()["id"]
        client.post(
            "/hierarchy/tasks",
            json={"name": "Task 1", "sprint_id": sprint_id, "prd_scope_item_id": "ref-001"},
        )

        response = client.get("/hierarchy/tree")
        assert response.status_code == 200
        tree = response.json()
        assert len(tree) >= 1
        assert tree[0]["type"] == "portfolio"
        assert len(tree[0]["children"]) >= 1
        assert tree[0]["children"][0]["type"] == "program"
        assert len(tree[0]["children"][0]["children"]) >= 1
        assert tree[0]["children"][0]["children"][0]["type"] == "project"


class TestAgentAPI:
    def test_register_agent(self):
        response = client.post(
            "/agents",
            json={
                "name": "test-agent",
                "agent_type": "general",
                "heartbeat_interval": 30,
                "capacity": 1,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test-agent"
        assert data["agent_type"] == "general"
        assert "id" in data

    def test_list_agents(self):
        client.post("/agents", json={"name": "Agent 1"})
        client.post("/agents", json={"name": "Agent 2"})
        response = client.get("/agents")
        assert response.status_code == 200
        assert len(response.json()) >= 2

    def test_record_heartbeat(self):
        ag_resp = client.post("/agents", json={"name": "Agent"})
        agent_id = ag_resp.json()["id"]

        response = client.post(
            f"/agents/{agent_id}/heartbeat",
            json={"status": "working", "task_id": None, "progress_note": "starting"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "working"
        assert data["agent_id"] == agent_id
        assert "timestamp" in data

    def test_get_heartbeat_timeline(self):
        ag_resp = client.post("/agents", json={"name": "Agent"})
        agent_id = ag_resp.json()["id"]

        client.post(f"/agents/{agent_id}/heartbeat", json={"status": "idle"})
        client.post(f"/agents/{agent_id}/heartbeat", json={"status": "working"})
        response = client.get(f"/agents/{agent_id}/heartbeats")
        assert response.status_code == 200
        heartbeats = response.json()
        assert len(heartbeats) == 2
        statuses = [h["status"] for h in heartbeats]
        assert "idle" in statuses
        assert "working" in statuses

    def test_agent_status_endpoint(self):
        ag_resp = client.post("/agents", json={"name": "Agent"})
        agent_id = ag_resp.json()["id"]

        response = client.get(f"/agents/{agent_id}/status")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == agent_id
        assert "status" in data
        assert "missed_heartbeats" in data

    def test_agent_not_found(self):
        response = client.get("/agents/nonexistent-id")
        assert response.status_code == 404