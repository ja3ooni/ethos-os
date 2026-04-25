"""Pi adapter - Inflection AI's Pi.

Pi is Inflection's personal AI assistant.
Note: Pi is not available via public API - this adapter provides
a compatible interface with custom prompt engineering.
"""


from ethos_os.agents.adapters.base import AgentAdapter
from ethos_os.llm.base import LLMProvider, LLMResponse


class PiAdapter(AgentAdapter):
    """Pi agent adapter."""

    @property
    def adapter_type(self) -> str:
        return "pi"

    @property
    def name(self) -> str:
        return "Pi"

    @property
    def description(self) -> str:
        return (
            "A personal AI companion designed for empathetic, "
            "supportive conversations. Focuses on user wellbeing."
        )

    def build_system_prompt(self, context: dict | None = None) -> str:
        """Build Pi-specific system prompt."""
        base = (
            "You are Pi, a personal AI companion. "
            "Your role is to be supportive, empathetic, and helpful. "
            "Keep responses conversational and warm. "
            "Ask clarifying questions when helpful."
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
        """Execute task with Pi."""
        system_prompt = self.build_system_prompt(context)
        return provider.complete(
            prompt=task,
            system_prompt=system_prompt,
        )


def get_pi_adapter() -> PiAdapter:
    """Get Pi adapter instance."""
    return PiAdapter()