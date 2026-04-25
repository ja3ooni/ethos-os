"""Orchestration tests.

Tests for:
- ORCH-01: Heartbeat-based task assignment
- ORCH-02: Capability matching
- ORCH-03: CEO Agent integration (skeleton for now)
- ORCH-04: Execution Agents autonomous
- ORCH-05: Failure detection
- ORCH-06: Initiative hierarchy gates
"""

import pytest
from uuid import uuid4

from ethos_os.db import Base, get_session
from ethos_os.models.gate import Gate, GateStatus
from ethos_os.models.task import Task, TaskStatus
from ethos_os.agents.registry import Agent
from ethos_os.execution.agent import Agent as ExecAgent
from ethos_os.orchestration.router import TaskRouter
from ethos_os.orchestration.task_queue import TaskQueue, TaskLockStatus
from ethos_os.orchestration.status_tracker import AgentStatusTracker, AgentWorkStatus
from ethos_os.orchestration.budget import BudgetEnforcer, BudgetAction
from ethos_os.orchestration.failure import FailureDetector, FailureType
from ethos_os.execution.orchestration import OrchestratedHeartbeat


@pytest.fixture
def session():
    """Create test session."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()


@pytest.fixture
def agent(session):
    """Create test agent."""
    agent = Agent(
        id=str(uuid4()),
        name="Test Execution Agent",
        role="execution",
        division="engineering",
        skills_summary="Test agent for orchestration tests",
        capabilities=["testing", "coding"],
        is_hired=True,
        max_monthly_budget_usd="100.00",
    )
    session.add(agent)
    session.commit()
    return agent


@pytest.fixture
def task(session, agent):
    """Create test task."""
    task = Task(
        id=str(uuid4()),
        name="Test Task",
        sprint_id=str(uuid4()),
        prd_scope_item_id=str(uuid4()),
        assignee_id=agent.id,
        status=TaskStatus.TODO.value,
    )
    session.add(task)
    session.commit()
    return task


class TestTaskRouter:
    """Test task router (ORCH-02)."""

    def test_match_task_returns_agents(self, session, agent, task):
        """Test capability matching."""
        router = TaskRouter(session)
        candidates = router.match_task_to_agents(
            task.id,
            required_capabilities=["testing"],
        )
        assert len(candidates) >= 1

    def test_assign_best_agent(self, session, agent, task):
        """Test assignment to cheapest agent."""
        router = TaskRouter(session)
        assigned_id = router.assign_best_agent(
            task.id,
            required_capabilities=["testing"],
        )
        assert assigned_id is not None

        task = session.get(Task, task.id)
        assert task.assignee_id == assigned_id


class TestTaskQueue:
    """Test task queue with locks (ORCH-01)."""

    def test_checkout_claims_task(self, session, agent, task):
        """Test atomic checkout."""
        from ethos_os.orchestration.task_queue import TaskLock
        queue = TaskQueue(session)
        result = queue.checkout(task.id, agent.id)
        assert result is True

        lock = session.query(TaskLock).first()
        assert lock is not None

    def test_checkout_blocks_others(self, session, agent, task):
        """Test double-work prevention."""
        queue = TaskQueue(session)
        other_agent_id = str(uuid4())

        queue.checkout(task.id, agent.id)
        result = queue.checkout(task.id, other_agent_id)
        assert result is False

    def test_release_unclaims_task(self, session, agent, task):
        """Test release."""
        queue = TaskQueue(session)
        queue.checkout(task.id, agent.id)
        result = queue.release(task.id, agent.id)
        assert result is True


class TestAgentStatusTracker:
    """Test status tracker (ORCH-01)."""

    def test_idle_to_working_transition(self, session, agent):
        """Test idle -> working."""
        tracker = AgentStatusTracker(session)
        result = tracker.transition(
            agent.id, None, AgentWorkStatus.WORKING.value
        )
        assert result is True

        status = tracker.get_current_status(agent.id)
        assert status == AgentWorkStatus.WORKING.value

    def test_working_to_blocked_transition(self, session, agent):
        """Test working -> blocked."""
        tracker = AgentStatusTracker(session)
        tracker.transition(agent.id, None, AgentWorkStatus.WORKING.value)
        result = tracker.transition(
            agent.id, None, AgentWorkStatus.BLOCKED.value, "Gate pending"
        )
        assert result is True


class TestBudgetEnforcer:
    """Test budget enforcement (ORCH-04)."""

    def test_allow_under_budget(self, session, agent):
        """Test allowance under budget."""
        enforcer = BudgetEnforcer(session)
        action, msg = enforcer.check_budget(agent.id, 10.0)
        assert action == BudgetAction.ALLOW.value

    def test_warn_near_budget(self, session, agent):
        """Test warning at 80%."""
        from ethos_os.orchestration.budget import AgentSpendingRecord

        session.add(AgentSpendingRecord(
            id=str(uuid4()),
            agent_id=agent.id,
            task_id=None,
            call_cost_usd=81.0,
        ))
        session.commit()

        enforcer = BudgetEnforcer(session)
        action, msg = enforcer.check_budget(agent.id, 15.0)
        assert action == BudgetAction.WARN.value

    def test_record_spending(self, session, agent):
        """Test spending recording."""
        enforcer = BudgetEnforcer(session)
        record = enforcer.record_spending(agent.id, None, 0.05, 100)
        assert record is not None


class TestFailureDetector:
    """Test failure detection (ORCH-05)."""

    def test_detect_missed_heartbeats(self, session, agent):
        """Test missed heartbeats detection."""
        exec_agent = ExecAgent(
            id=agent.id,
            name=agent.name,
            agent_type="execution",
            status="idle",
            missed_heartbeats=5,
        )
        session.add(exec_agent)
        session.commit()

        detector = FailureDetector(session)
        failures = detector.detect_failures(agent.id)
        assert len(failures) >= 1
        assert failures[0]["type"] == FailureType.MISSED_HEARTBEAT.value

    def test_reassign_tasks(self, session, agent, task):
        """Test task reassignment."""
        detector = FailureDetector(session)
        new_agent_id = str(uuid4())
        reassigned = detector.reassign_tasks(agent.id, new_agent_id)
        assert len(reassigned) >= 1


class TestOrchestratedHeartbeat:
    """Test heartbeat with orchestration."""

    def test_heartbeat_with_no_tasks(self, session, agent):
        """Test heartbeat returns idle when no tasks."""
        heartbeat = OrchestratedHeartbeat(session)
        result = heartbeat.heartbeat_cycle(agent.id)
        assert result["task_executed"] is False

    def test_heartbeat_with_blocked_task(self, session, agent, task):
        """Test heartbeat blocks on gate."""
        gate = Gate(
            id=str(uuid4()),
            name="Test Gate",
            gate_type="approval",
            status=GateStatus.PENDING.value,
            entity_id=task.id,
        )
        session.add(gate)
        session.commit()

        heartbeat = OrchestratedHeartbeat(session)
        result = heartbeat.heartbeat_cycle(agent.id)

        assert result["blocked"] is True
        assert "gate" in result["reason"].lower()