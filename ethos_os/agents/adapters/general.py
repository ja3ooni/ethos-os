"""General agent adapter - fallback for general tasks."""


from ethos_os.agents.adapters.base import AgentAdapter
from ethos_os.llm.base import LLMProvider, LLMResponse


class GeneralAgentAdapter(AgentAdapter):
    """General agent adapter - fallback."""

    @property
    def adapter_type(self) -> str:
        return "general"

    @property
    def name(self) -> str:
        return "General Agent"

    @property
    def description(self) -> str:
        return (
            "A general-purpose AI assistant for task execution. "
            "Versatile and adaptable to various tasks."
        )

    def build_system_prompt(self, context: dict | None = None) -> str:
        """Build general system prompt."""
        base = (
            "You are a general-purpose AI assistant. "
            "Your role is to complete tasks efficiently and accurately. "
            "When unclear, ask for clarification. "
            "Provide clear, actionable responses."
        )
        if context:
            context_info = self._format_context(context)
            return f"{base}\n\nContext:\n{context_info}"
        return base

    def execute(
        self,
        task: str,
        provider: LLMProvider,
        context: dict | None = None,
    ) -> LLMResponse:
        """Execute task."""
        system_prompt = self.build_system_prompt(context)
        return provider.complete(
            prompt=task,
            system_prompt=system_prompt,
        )


def get_general_adapter() -> GeneralAgentAdapter:
    """Get General adapter instance."""
    return GeneralAgentAdapter()