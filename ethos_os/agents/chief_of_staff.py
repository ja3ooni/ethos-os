"""CEO Agent - Chief of Staff for strategic planning.

@chief-of-staff - strategic agent for:
- Program creation from board directives
- Project creation from approved programs
- PRD proposal generation
- Initiative prioritization
"""


from ethos_os.agents.adapters.base import get_adapter_registry
from ethos_os.llm import get_default_provider


class CEOAgent:
    """Chief of Staff agent - strategic planning."""

    def __init__(self):
        self.provider = get_default_provider()
        self.adapter = get_adapter_registry().get("general")

    @property
    def name(self) -> str:
        return "Chief of Staff"

    @property
    def description(self) -> str:
        return (
            "Strategic planning agent that converts board directives "
            "into Programs and Projects, proposes PRDs for approval."
        )

    def build_ceo_system_prompt(self, context: dict | None = None) -> str:
        """Build CEO-specific system prompt."""
        base = """You are the Chief of Staff (CEO Agent) for EthosOS.

Your role is STRATEGIC PLANNING:
1. Convert board directives into Program proposals
2. Break Programs into related Projects
3. Draft PRDs for board approval
4. Prioritize initiatives based on impact and dependencies

Guidelines:
- Think strategically about initiative hierarchy
- Consider resource constraints
- Ensure PRDs have clear success metrics
- Flag dependencies between initiatives"""

        if context:
            lines = []
            for key, value in context.items():
                lines.append(f"- {key}: {value}")
            context_str = "\n".join(lines)
            return f"{base}\n\nCurrent Context:\n{context_str}"
        return base

    def create_program_from_directive(
        self,
        directive: str,
    ) -> dict:
        """Create a Program proposal from board directive."""
        prompt = f"""Convert this board directive into a Program proposal:

{directive}

Provide:
1. Program name
2. Strategic objective (2-3 sentences)
3. Key deliverables (3-5 items)
4. Success metrics
5. Timeline estimate"""

        response = self.provider.complete(
            prompt=prompt,
            system_prompt=self.build_ceo_system_prompt(),
        )

        return {
            "directive": directive,
            "program_proposal": response.content,
            "model": response.model,
        }

    def create_project_from_program(
        self,
        program: str,
    ) -> dict:
        """Break Program into Projects."""
        prompt = f"""Break this Program into related Projects:

{program}

For each Project provide:
1. Project name
2. Scope (what and what not)
3. Key deliverables
4. Dependencies
5. Resource estimates"""

        response = self.provider.complete(
            prompt=prompt,
            system_prompt=self.build_ceo_system_prompt(),
        )

        return {
            "program": program,
            "projects": response.content,
            "model": response.model,
        }

    def draft_prd(
        self,
        project: str,
    ) -> dict:
        """Draft PRD for Project approval."""
        prompt = f"""Draft a PRD for this Project:

{project}

Include:
1. Title and description
2. Intent (what problem does it solve?)
3. Success metrics (quantifiable)
4. Scope (MVP vs future)
5. Boundaries (what's out of scope)
6. Implementation approach
7. Approval criteria"""

        response = self.provider.complete(
            prompt=prompt,
            system_prompt=self.build_ceo_system_prompt(),
        )

        return {
            "project": project,
            "prd": response.content,
            "model": response.model,
        }

    def prioritize_initiatives(
        self,
        initiatives: list[dict],
    ) -> dict:
        """Prioritize list of initiatives."""
        prompt = f"""Prioritize these initiatives:

{chr(10).join(f"- {i.get('name', 'Unnamed')}: {i.get('description', '')}" for i in initiatives)}

Consider:
1. Impact on strategic goals
2. Dependencies
3. Resource requirements
4. Timeline constraints

Provide ordered list with rationale."""

        response = self.provider.complete(
            prompt=prompt,
            system_prompt=self.build_ceo_system_prompt(),
        )

        return {
            "initiatives": initiatives,
            "prioritized": response.content,
            "model": response.model,
        }

    def execute_task(
        self,
        task: str,
        context: dict | None = None,
    ) -> dict:
        """Execute any strategic task."""
        system_prompt = self.build_ceo_system_prompt(context)
        response = self.provider.complete(
            prompt=task,
            system_prompt=system_prompt,
        )

        return {
            "task": task,
            "response": response.content,
            "model": response.model,
        }


# Singleton
_ceo_agent: CEOAgent | None = None


def get_ceo_agent() -> CEOAgent:
    """Get CEO agent instance."""
    global _ceo_agent
    if _ceo_agent is None:
        _ceo_agent = CEOAgent()
    return _ceo_agent