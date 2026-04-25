"""Budget enforcement per agent.

ORCH-04: Budget tracking per agent - prevent overspend.
Tracks spending against allocated budget.
"""

import enum
from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import Column, DateTime, Numeric, String, JSON
from sqlalchemy.orm import Session

from ethos_os.db import Base


class BudgetAction(enum.Enum):
    """Budget action."""
    ALLOW = "allow"
    WARN = "warn"
    DENY = "deny"


class AgentSpendingRecord(Base):
    """Agent spending record for budget tracking.

    Tracks each call/inference cost against budget.
    """

    __tablename__ = "agent_spending"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    agent_id = Column(String(36), nullable=False, index=True)
    task_id = Column(String(36), nullable=True, index=True)
    call_cost_usd = Column(Numeric(10, 6), nullable=False)
    tokens_used = Column(Numeric(10, 2), nullable=True)
    call_metadata = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<AgentSpending(agent={self.agent_id}, cost=${self.call_cost_usd})>"


class BudgetEnforcer:
    """Budget enforcement per agent.

    Requirements:
    - ORCH-04: Budget tracking per agent
    - WARN on 80% budget, DENY on 100%
    """

    WARN_THRESHOLD = 0.80
    DENY_THRESHOLD = 1.00

    def __init__(self, session: Session):
        self.session = session

    def check_budget(
        self,
        agent_id: str,
        proposed_cost_usd: float,
    ) -> tuple[str, str]:
        """Check if budget allows proposed cost.

        Returns (action, message).
        - ALLOW: Under budget
        - WARN: Over 80% budget
        - DENY: Would exceed budget
        """
        from ethos_os.agents.registry import Agent

        agent = self.session.query(Agent).where(Agent.id == agent_id).first()
        if not agent:
            return BudgetAction.ALLOW.value, "Agent not found, allowing"

        budget_str = agent.max_monthly_budget_usd
        if not budget_str or budget_str == "":
            return BudgetAction.ALLOW.value, "No budget set, allowing"

        budget = float(budget_str)
        current_spend = self.get_total_spend(agent_id)
        projected = current_spend + proposed_cost_usd

        if projected >= budget * self.DENY_THRESHOLD:
            return BudgetAction.DENY.value, f"Would exceed ${budget} budget"
        if projected >= budget * self.WARN_THRESHOLD:
            return BudgetAction.WARN.value, f"Near ${budget} budget limit"
        return BudgetAction.ALLOW.value, f"Under ${budget} budget"

    def record_spending(
        self,
        agent_id: str,
        task_id: str | None,
        cost_usd: float,
        tokens_used: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AgentSpendingRecord:
        """Record spending for an agent/task."""
        record = AgentSpendingRecord(
            id=str(uuid4()),
            agent_id=agent_id,
            task_id=task_id,
            call_cost_usd=cost_usd,
            tokens_used=tokens_used,
            metadata=metadata,
        )
        self.session.add(record)
        self.session.flush()
        return record

    def get_total_spend(
        self,
        agent_id: str,
        since: datetime | None = None,
    ) -> float:
        """Get total spend for an agent since datetime."""
        query = self.session.query(AgentSpendingRecord).where(
            AgentSpendingRecord.agent_id == agent_id
        )

        if since:
            query = query.where(AgentSpendingRecord.timestamp >= since)

        total = query.with_entities(
            self.session.query(AgentSpendingRecord)
            .where(AgentSpendingRecord.agent_id == agent_id)
        ).scalar()

        if total is None:
            total = 0.0

        records = self.session.execute(
            self.session.query(AgentSpendingRecord)
            .where(AgentSpendingRecord.agent_id == agent_id)
            .where(
                (since is None) | (AgentSpendingRecord.timestamp >= since)
            )
        ).scalars().all()

        total = sum(float(r.call_cost_usd) for r in records)
        return total

    def get_remaining_budget(
        self,
        agent_id: str,
    ) -> dict:
        """Get remaining budget for agent."""
        from ethos_os.agents.registry import Agent

        agent = self.session.query(Agent).where(Agent.id == agent_id).first()
        if not agent:
            return {"remaining": 0, "budget": 0, "pct": 0}

        budget_str = agent.max_monthly_budget_usd
        if not budget_str or budget_str == "":
            return {"remaining": 0, "budget": 0, "pct": 0, "unlimited": True}

        budget = float(budget_str)
        spent = self.get_total_spend(agent_id)
        remaining = max(0, budget - spent)

        return {
            "remaining": remaining,
            "budget": budget,
            "spent": spent,
            "pct": (spent / budget * 100) if budget > 0 else 0,
        }


def get_budget_enforcer(session: Session) -> BudgetEnforcer:
    """Get budget enforcer instance."""
    return BudgetEnforcer(session)