"""Integration tests for heartbeat system."""

import pytest


from ethos_os.execution.agent import Agent, AgentStatus
from ethos_os.execution.heartbeat import Heartbeat
from ethos_os.execution.scheduler import AgentRegistry
from ethos_os.execution.executor import AgentExecutor
from ethos_os.execution.failure import FailureDetector
from ethos_os.models.gate import GateRequest, GateStatus, GateType
from ethos_os.models.task import Task, TaskStatus
from ethos_os.db import get_engine, get_session_factory, Base


@pytest.fixture
def session():
    """Create a test database session."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


class TestAgentRegistry:
    """Tests for AgentRegistry."""

    def test_create_agent(self, session):
        """Test agent registration."""
        registry = AgentRegistry(session)
        agent = registry.create(
            agent_id="agent-001",
            name="Test Agent",
            agent_type="general",
            heartbeat_interval=30,
            capacity=1,
        )
        session.commit()

        assert agent.id == "agent-001"
        assert agent.name == "Test Agent"
        assert agent.status == AgentStatus.IDLE.value
        assert agent.heartbeat_interval == 30

    def test_get_agent(self, session):
        """Test getting an agent."""
        registry = AgentRegistry(session)
        registry.create(
            agent_id="agent-001",
            name="Test Agent",
        )
        session.commit()

        agent = registry.get("agent-001")
        assert agent is not None
        assert agent.name == "Test Agent"

    def test_update_status(self, session):
        """Test updating agent status."""
        registry = AgentRegistry(session)
        registry.create(
            agent_id="agent-001",
            name="Test Agent",
        )
        session.commit()

        registry.update_status("agent-001", AgentStatus.WORKING.value, "task-001")
        agent = registry.get("agent-001")

        assert agent.status == AgentStatus.WORKING.value
        assert agent.current_task_id == "task-001"

    def test_min_heartbeat_interval(self, session):
        """Test minimum heartbeat interval enforced."""
        registry = AgentRegistry(session)
        agent = registry.create(
            agent_id="agent-001",
            name="Test Agent",
            heartbeat_interval=5,
        )
        session.commit()

        assert agent.heartbeat_interval == 10

    def test_increment_missed_heartbeats(self, session):
        """Test incrementing missed heartbeat count."""
        registry = AgentRegistry(session)
        registry.create(agent_id="agent-001", name="Test Agent")
        session.commit()

        count = registry.increment_missed_heartbeats("agent-001")
        assert count == 1

        count = registry.increment_missed_heartbeats("agent-001")
        assert count == 2

    def test_get_dead_agents(self, session):
        """Test finding dead agents."""
        registry = AgentRegistry(session)
        registry.create(agent_id="agent-001", name="Test Agent")
        session.commit()

        registry.increment_missed_heartbeats("agent-001")
        registry.increment_missed_heartbeats("agent-001")
        registry.increment_missed_heartbeats("agent-001")
        session.commit()

        dead = registry.get_dead_agents()
        assert len(dead) == 1
        assert dead[0].id == "agent-001"


class TestHeartbeats:
    """Tests for heartbeat recording."""

    def test_record_heartbeat(self, session):
        """Test recording a heartbeat."""
        registry = AgentRegistry(session)
        registry.create(agent_id="agent-001", name="Test Agent")
        session.commit()

        heartbeat = Heartbeat(
            id="hb-001",
            agent_id="agent-001",
            status=AgentStatus.WORKING.value,
            task_id="task-001",
            progress_note="Working on task",
        )
        session.add(heartbeat)
        session.commit()

        assert heartbeat.id == "hb-001"
        assert heartbeat.agent_id == "agent-001"
        assert heartbeat.status == AgentStatus.WORKING.value

    def test_heartbeat_payload(self, session):
        """Test heartbeat payload data."""
        registry = AgentRegistry(session)
        registry.create(agent_id="agent-001", name="Test Agent")
        session.commit()

        heartbeat = Heartbeat(
            id="hb-001",
            agent_id="agent-001",
            status=AgentStatus.WORKING.value,
            task_id="task-001",
            progress_note="Progress update",
        )
        session.add(heartbeat)

        payload = heartbeat.payload_data
        assert payload["agent_id"] == "agent-001"
        assert payload["status"] == "working"
        assert payload["task_id"] == "task-001"


class TestAgentExecutor:
    """Tests for agent executor."""

    def test_execute_no_tasks(self, session):
        """Test execution when no tasks assigned."""
        registry = AgentRegistry(session)
        registry.create(agent_id="agent-001", name="Test Agent")
        session.commit()

        executor = AgentExecutor(session)
        result = executor.execute_cycle("agent-001")

        assert result.task_executed is False
        assert result.blocked is False

    def test_execute_with_task(self, session):
        """Test execution with an assigned task."""
        from uuid import uuid4

        registry = AgentRegistry(session)
        registry.create(agent_id="agent-001", name="Test Agent")

        task = Task(
            id=str(uuid4()),
            name="Test Task",
            sprint_id=str(uuid4()),
            prd_scope_item_id=str(uuid4()),
            status=TaskStatus.TODO.value,
            assignee_id="agent-001",
            path=f"/{uuid4()}/",
            path_depth=5,
        )
        session.add(task)
        session.commit()

        executor = AgentExecutor(session)
        result = executor.execute_cycle("agent-001")

        assert result.task_executed is True
        assert result.task_id == task.id
        assert result.blocked is False

    def test_blocked_by_gate(self, session):
        """Test execution blocked by pending gate."""
        from uuid import uuid4

        registry = AgentRegistry(session)
        registry.create(agent_id="agent-001", name="Test Agent")

        task_id = str(uuid4())
        task = Task(
            id=task_id,
            name="Test Task",
            sprint_id=str(uuid4()),
            prd_scope_item_id=str(uuid4()),
            status=TaskStatus.TODO.value,
            assignee_id="agent-001",
            path=f"/{uuid4()}/",
            path_depth=5,
        )
        session.add(task)

        gate = GateRequest(
            id=str(uuid4()),
            gate_type=GateType.SCOPE.value,
            entity_id=task_id,
            entity_type="task",
            status=GateStatus.PENDING.value,
            trigger_condition='{"reason": "scope change"}',
            timeout_hours=48,
        )
        session.add(gate)
        session.commit()

        executor = AgentExecutor(session)
        result = executor.execute_cycle("agent-001")

        assert result.blocked is True
        assert "Pending" in result.reason

    def test_can_execute_task(self, session):
        """Test checking if task can be executed."""
        from uuid import uuid4

        task_id = str(uuid4())

        can_exec = AgentExecutor(session).can_execute_task(task_id)
        assert can_exec is True

        gate = GateRequest(
            id=str(uuid4()),
            gate_type=GateType.SCOPE.value,
            entity_id=task_id,
            entity_type="task",
            status=GateStatus.PENDING.value,
            timeout_hours=48,
        )
        session.add(gate)
        session.commit()

        can_exec = AgentExecutor(session).can_execute_task(task_id)
        assert can_exec is False


class TestFailureDetector:
    """Tests for failure detection."""

    def test_check_for_dead_agents(self, session):
        """Test finding dead agents."""
        registry = AgentRegistry(session)
        registry.create(agent_id="agent-001", name="Agent 1")
        registry.create(agent_id="agent-002", name="Agent 2")
        session.commit()

        registry.increment_missed_heartbeats("agent-001")
        registry.increment_missed_heartbeats("agent-001")
        registry.increment_missed_heartbeats("agent-001")
        session.commit()

        detector = FailureDetector(session)
        dead = detector.check_for_dead_agents()

        assert len(dead) == 1
        assert dead[0].id == "agent-001"

    def test_trigger_reassignment(self, session):
        """Test triggering reassignment."""
        from uuid import uuid4

        registry = AgentRegistry(session)
        registry.create(agent_id="agent-001", name="Test Agent")
        session.commit()

        registry.increment_missed_heartbeats("agent-001")
        registry.increment_missed_heartbeats("agent-001")
        registry.increment_missed_heartbeats("agent-001")

        task_id = str(uuid4())
        task = Task(
            id=task_id,
            name="Test Task",
            sprint_id=str(uuid4()),
            prd_scope_item_id=str(uuid4()),
            status=TaskStatus.IN_PROGRESS.value,
            assignee_id="agent-001",
            path=f"/{uuid4()}/",
            path_depth=5,
        )
        session.add(task)
        session.commit()

        detector = FailureDetector(session)
        dead_agent = session.get(Agent, "agent-001")
        reassigned = detector.trigger_reassignment(dead_agent)

        assert task_id in reassigned

        session.refresh(task)
        assert task.assignee_id is None
        assert task.status == TaskStatus.BLOCKED.value


class TestStatusTransitions:
    """Tests for status transitions."""

    def test_status_idle_to_working(self, session):
        """Test idle to working transition."""
        from uuid import uuid4

        registry = AgentRegistry(session)
        agent = registry.create(
            agent_id="agent-001",
            name="Test Agent",
            heartbeat_interval=30,
        )
        agent.status = AgentStatus.IDLE.value
        session.commit()

        executor = AgentExecutor(session)
        task = Task(
            id=str(uuid4()),
            name="Test Task",
            sprint_id=str(uuid4()),
            prd_scope_item_id=str(uuid4()),
            assignee_id="agent-001",
            path=f"/{uuid4()}/",
            path_depth=5,
        )
        session.add(task)
        session.commit()

        result = executor.execute_cycle("agent-001")

        assert result.task_executed is True

        updated_agent = registry.get("agent-001")
        assert updated_agent.status == AgentStatus.WORKING.value

    def test_status_working_to_blocked(self, session):
        """Test working to blocked transition."""
        from uuid import uuid4

        task_id = str(uuid4())

        registry = AgentRegistry(session)
        agent = registry.create(
            agent_id="agent-001",
            name="Test Agent",
        )
        agent.status = AgentStatus.WORKING.value
        agent.current_task_id = task_id

        task = Task(
            id=task_id,
            name="Test Task",
            sprint_id=str(uuid4()),
            prd_scope_item_id=str(uuid4()),
            assignee_id="agent-001",
            status=TaskStatus.IN_PROGRESS.value,
            path=f"/{uuid4()}/",
            path_depth=5,
        )
        session.add(task)

        gate = GateRequest(
            id=str(uuid4()),
            gate_type=GateType.BUDGET.value,
            entity_id=task_id,
            entity_type="task",
            status=GateStatus.PENDING.value,
            timeout_hours=24,
        )
        session.add(gate)
        session.commit()

        executor = AgentExecutor(session)
        result = executor.execute_cycle("agent-001")

        assert result.blocked is True

        updated_agent = registry.get("agent-001")
        assert updated_agent.status == AgentStatus.BLOCKED.value