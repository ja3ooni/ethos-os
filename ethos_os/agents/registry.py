"""Agent registry with token-efficient architecture.

Design principles:
1. Summary-first: Never inject full prompts in listings
2. Lazy loading: Fetch full config only at execution
3. SQLite primary: Fast lookups, minimal context
4. Qdrant for matching: Semantic search without token bloat
5. Working memory cache: Keep execution configs nearby
"""

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import Column, DateTime, Index, String, Text, JSON, Boolean
from sqlalchemy.orm import Session

from ethos_os.db import Base, get_session as db_session


class Agent(Base):
    """Agent registry entry - token-efficient storage."""

    __tablename__ = "agents_registry"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), nullable=False)

    # Role hierarchy
    role = Column(String(50), nullable=False)  # ceo, lead, execution, specialist
    division = Column(String(100), nullable=False)  # engineering, sales, marketing, etc.

    # Token-efficient summaries (NOT full prompts)
    skills_summary = Column(Text, nullable=False)  # 1-2 sentences max
    capabilities = Column(JSON, nullable=False, default=list)  # ["coding", "api-design"]
    specialization = Column(String(255), nullable=True)  # "Python", "React", "Sales"

    # Cost tracking
    avg_response_tokens = Column(String(36), nullable=False, default="1000")
    cost_per_call_usd = Column(String(10), nullable=False, default="0.01")

    # Agent source reference (agency-agents file path)
    source_path = Column(String(500), nullable=True)  # e.g., "engineering/senior-developer.md"

    # System prompt reference (NOT stored in SQLite for token efficiency)
    prompt_reference = Column(String(255), nullable=True)  # Key to fetch from cache/storage

    # Status
    is_active = Column(Boolean, default=True)
    is_hired = Column(Boolean, default=False)  # Hired into this company

    # Hiring info
    hired_at = Column(DateTime(timezone=True), nullable=True)
    salary_usd = Column(String(36), nullable=True)  # Budget allocation
    max_monthly_budget_usd = Column(String(36), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_agents_role", "role"),
        Index("ix_agents_division", "division"),
        Index("ix_agents_active", "is_active"),
        Index("ix_agents_hired", "is_hired"),
        Index("ix_agents_capabilities", "capabilities", postgresql_using="gin"),
    )


class AgentRepository:
    """Token-efficient agent repository."""

    def __init__(self, session: Session):
        self.session = session

    def list_for_task(
        self,
        role: str | None = None,
        division: str | None = None,
        capabilities: list[str] | None = None,
        hired_only: bool = True,
        limit: int = 20,
    ) -> list[dict]:
        """List agents for task assignment - TOKEN EFFICIENT.

        Returns summary only, NOT full prompts.
        Use this for listings, selection UI, task assignment.
        """
        query = self.session.query(Agent).where(Agent.is_active == True)

        if hired_only:
            query = query.where(Agent.is_hired == True)
        if role:
            query = query.where(Agent.role == role)
        if division:
            query = query.where(Agent.division == division)
        if capabilities:
            # Filter by capabilities (JSON array)
            for cap in capabilities:
                query = query.where(Agent.capabilities.contains(cap))

        agents = query.limit(limit).all()

        # Return SUMMARY only - no full prompts
        return [
            {
                "id": a.id,
                "name": a.name,
                "role": a.role,
                "division": a.division,
                "skills_summary": a.skills_summary,
                "capabilities": a.capabilities,
                "specialization": a.specialization,
                "cost_per_call_usd": a.cost_per_call_usd,
                "last_used_at": a.last_used_at.isoformat() if a.last_used_at else None,
            }
            for a in agents
        ]

    def get_for_execution(self, agent_id: str) -> dict | None:
        """Fetch agent for execution - FULL CONFIG.

        This is called ONLY when executing, not in listings.
        Returns full config including prompt_reference.
        """
        agent = self.session.query(Agent).where(Agent.id == agent_id).first()
        if not agent:
            return None

        return {
            "id": agent.id,
            "name": agent.name,
            "role": agent.role,
            "division": agent.division,
            "skills_summary": agent.skills_summary,
            "capabilities": agent.capabilities,
            "specialization": agent.specialization,
            "source_path": agent.source_path,
            "prompt_reference": agent.prompt_reference,
            "cost_per_call_usd": agent.cost_per_call_usd,
        }

    def search_by_capability(self, query: str, limit: int = 10) -> list[dict]:
        """Semantic search for agents by capability.

        Uses Qdrant for embeddings, but returns summary only.
        """
        # TODO: Implement Qdrant semantic search
        # For now, SQLite text search on summary
        agents = (
            self.session.query(Agent)
            .where(Agent.is_active == True, Agent.is_hired == True)
            .where(
                (Agent.skills_summary.ilike(f"%{query}%"))
                | (Agent.capabilities.contains(query))
            )
            .limit(limit)
            .all()
        )

        return [
            {
                "id": a.id,
                "name": a.name,
                "role": a.role,
                "skills_summary": a.skills_summary,
                "capabilities": a.capabilities,
            }
            for a in agents
        ]

    def hire(
        self,
        source_path: str,
        name: str,
        role: str,
        division: str,
        skills_summary: str,
        capabilities: list[str],
        specialization: str | None = None,
        max_monthly_budget_usd: str | None = None,
    ) -> Agent:
        """Hire an agent from agency-agents into this company."""
        agent = Agent(
            name=name,
            role=role,
            division=division,
            skills_summary=skills_summary,
            capabilities=capabilities,
            specialization=specialization,
            source_path=source_path,
            is_hired=True,
            hired_at=datetime.utcnow(),
            max_monthly_budget_usd=max_monthly_budget_usd,
        )
        self.session.add(agent)
        self.session.commit()
        return agent

    def fire(self, agent_id: str) -> bool:
        """Terminate an agent."""
        agent = self.session.query(Agent).where(Agent.id == agent_id).first()
        if agent:
            agent.is_hired = False
            agent.hired_at = None
            self.session.commit()
            return True
        return False

    def update_last_used(self, agent_id: str) -> None:
        """Track agent usage for analytics."""
        agent = self.session.query(Agent).where(Agent.id == agent_id).first()
        if agent:
            agent.last_used_at = datetime.utcnow()
            self.session.commit()


# Singleton instance
_agent_repo: AgentRepository | None = None


def get_agent_repository() -> AgentRepository:
    """Get agent repository instance."""
    global _agent_repo
    if _agent_repo is None:
        _agent_repo = AgentRepository(db_session().__enter__())
    return _agent_repo


# Import agency-agents metadata (TOKEN EFFICIENT)
def import_agents_from_agency_repo(agency_repo_path: str) -> int:
    """Import agent metadata from agency-agents repo.

    Parses only YAML frontmatter - NOT full prompts.
    This is token-efficient: we store summaries, not full content.
    """
    import os
    import re
    import yaml

    count = 0
    session = db_session().__enter__()

    for root, dirs, files in os.walk(agency_repo_path):
        # Skip hidden and non-agent directories
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["scripts", "integrations", ".opencode"]]

        for file in files:
            if not file.endswith(".md"):
                continue

            file_path = os.path.join(root, file)

            # Skip non-agent files
            if file in ["AGENTS.md", "README.md", "CONTRIBUTING.md"]:
                continue

            try:
                with open(file_path, "r") as f:
                    content = f.read()

                # Parse YAML frontmatter
                match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
                if not match:
                    continue

                frontmatter = yaml.safe_load(match.group(1))
                if not frontmatter:
                    continue

                # Extract token-efficient metadata
                name = frontmatter.get("name", file.replace(".md", ""))
                description = frontmatter.get("description", "")

                # Determine role and division from path
                rel_path = os.path.relpath(file_path, agency_repo_path)
                parts = rel_path.split(os.sep)
                division = parts[0] if len(parts) > 1 else "specialized"

                # Map to standard roles
                role = _infer_role(name, description, division)

                # Extract capabilities from description
                capabilities = _extract_capabilities(description)

                # Create summary (truncate to 200 chars)
                skills_summary = description[:200] if len(description) > 200 else description

                # Check if already exists
                existing = session.query(Agent).where(Agent.source_path == rel_path).first()
                if existing:
                    continue

                # Create summary entry only
                agent = Agent(
                    name=name,
                    role=role,
                    division=division,
                    skills_summary=skills_summary,
                    capabilities=capabilities,
                    source_path=rel_path,
                    is_active=True,
                )
                session.add(agent)
                count += 1

            except Exception:
                continue

    session.commit()
    return count


def _infer_role(name: str, description: str, division: str) -> str:
    """Infer agent role from name and description."""
    name_lower = name.lower()
    desc_lower = description.lower()

    if any(x in name_lower for x in ["chief", "ceo", "director", "head"]):
        return "ceo"
    if any(x in name_lower for x in ["lead", "manager", "principal"]):
        return "lead"
    if any(x in desc_lower for x in ["executing", "implementation", "build"]):
        return "execution"
    if any(x in desc_lower for x in ["research", "analysis", "analytics"]):
        return "research"
    if any(x in desc_lower for x in ["design", "creative", "ui"]):
        return "design"
    return "specialist"


def _extract_capabilities(text: str) -> list[str]:
    """Extract capabilities from description text."""
    # Simple keyword extraction
    capability_keywords = [
        "python", "javascript", "typescript", "react", "api", "database",
        "sales", "marketing", "analytics", "design", "security",
        "devops", "testing", "documentation", "research", "writing",
        "management", "planning", "strategy", "analysis", "coding",
    ]

    text_lower = text.lower()
    found = [kw for kw in capability_keywords if kw in text_lower]
    return found[:10]  # Max 10 capabilities