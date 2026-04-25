"""Agent registry tests - Phase 1: AGENT-01 through AGENT-04."""

import pytest
from ethos_os.db import Base, get_engine, get_session
from ethos_os.agents.registry import AgentRepository, Agent, import_agents_from_agency_repo


@pytest.fixture
def setup_db():
    """Create fresh DB for tests."""
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


class TestAgentRepository:
    """Test AGENT-01: Agent registry model and repository."""

    def test_create_agent(self, setup_db):
        """Test creating an agent in SQLite."""
        with get_session() as session:
            repo = AgentRepository(session)
            
            agent = repo.hire(
                source_path="engineering/dev.md",
                name="Senior Developer",
                role="execution",
                division="engineering",
                skills_summary="Expert in Python and TypeScript full-stack development.",
                capabilities=["python", "typescript", "react", "database"],
                specialization="Python",
                max_monthly_budget_usd="500",
            )

            assert agent.id is not None
            assert agent.name == "Senior Developer"
            assert agent.role == "execution"
            assert agent.is_hired is True
            assert agent.hired_at is not None

    def test_list_for_task_summary_only(self, setup_db):
        """Test AGENT-02: Summary-only listings - never full prompts in listings."""
        with get_session() as session:
            repo = AgentRepository(session)
            
            # Create test agents
            repo.hire(
                source_path="engineering/dev.md",
                name="Senior Developer",
                role="execution",
                division="engineering",
                skills_summary="Expert in Python and TypeScript full-stack development.",
                capabilities=["python", "typescript", "react"],
            )
            repo.hire(
                source_path="sales/closer.md",
                name="Sales Closer",
                role="execution",
                division="sales",
                skills_summary="Expert at closing enterprise deals.",
                capabilities=["sales", "negotiation"],
            )

        with get_session() as session:
            repo = AgentRepository(session)
            listing = repo.list_for_task(role="execution")

            # Verify summaries only - NO full prompts
            assert len(listing) == 2
            for agent in listing:
                assert "skills_summary" in agent
                assert agent["skills_summary"]  # Has summary
                assert "prompt_reference" not in agent  # Never in listings
                assert "source_path" not in agent  # Source not in listings

    def test_get_for_execution_full_config(self, setup_db):
        """Test AGENT-03: Lazy loading - full config only at execution."""
        with get_session() as session:
            repo = AgentRepository(session)
            agent = repo.hire(
                source_path="engineering/dev.md",
                name="Senior Developer",
                role="execution",
                division="engineering",
                skills_summary="Expert in Python.",
                capabilities=["python"],
                specialization="Python",
            )

        with get_session() as session:
            repo = AgentRepository(session)
            full = repo.get_for_execution(agent.id)

            # Full config at execution time
            assert full is not None
            assert "prompt_reference" in full
            assert "source_path" in full

    def test_hire_and_fire_lifecycle(self, setup_db):
        """Test AGENT-04/Lifecycle: Hiring/firing workflow."""
        with get_session() as session:
            repo = AgentRepository(session)
            agent = repo.hire(
                source_path="engineering/dev.md",
                name="Senior Developer",
                role="execution",
                division="engineering",
                skills_summary="Expert in Python.",
                capabilities=["python"],
            )

        with get_session() as session:
            repo = AgentRepository(session)
            # Verify hired
            listing = repo.list_for_task(hired_only=True)
            assert len(listing) == 1

            # Fire the agent
            fired = repo.fire(agent.id)
            assert fired is True

            # Verify fired
            listing = repo.list_for_task(hired_only=True)
            assert len(listing) == 0

    def test_search_by_capability(self, setup_db):
        """Search agents by capability."""
        with get_session() as session:
            repo = AgentRepository(session)
            repo.hire(
                source_path="engineering/dev.md",
                name="Python Developer",
                role="execution",
                division="engineering",
                skills_summary="Expert in Python development.",
                capabilities=["python", "api"],
            )
            repo.hire(
                source_path="design/ui.md",
                name="UI Designer",
                role="design",
                division="design",
                skills_summary="Expert in UI/UX design.",
                capabilities=["design", "ui"],
            )

        with get_session() as session:
            repo = AgentRepository(session)
            results = repo.search_by_capability("python")

            assert len(results) == 1
            assert results[0]["name"] == "Python Developer"

    def test_update_last_used(self, setup_db):
        """Track agent usage."""
        with get_session() as session:
            repo = AgentRepository(session)
            agent = repo.hire(
                source_path="engineering/dev.md",
                name="Senior Developer",
                role="execution",
                division="engineering",
                skills_summary="Expert in Python.",
                capabilities=["python"],
            )

        with get_session() as session:
            repo = AgentRepository(session)
            repo.update_last_used(agent.id)

        with get_session() as session:
            repo = AgentRepository(session)
            listing = repo.list_for_task()
            assert listing[0]["last_used_at"] is not None


class TestAgentImport:
    """Test import from agency-agents repo."""

    def test_import_agents_from_repo(self):
        """Test importing 147+ agents from agency-agents."""
        agency_path = "/Users/aljaunia/Documents/Develop/voiquyr/agency/agency-agents"
        
        count = import_agents_from_agency_repo(agency_path)
        
        # Should import 147+ agents
        assert count >= 100, f"Expected 147+, got {count}"