"""Hermes adapter - NousResearch's Hermes.

Hermes is an open-source assistant trained by Nous Research.
Can run via Ollama or direct API.
"""


from ethos_os.agents.adapters.base import AgentAdapter
from ethos_os.llm.base import LLMProvider, LLMResponse


class HermesAdapter(AgentAdapter):
    """Hermes agent adapter."""

    @property
    def adapter_type(self) -> str:
        return "hermes"

    @property
    def name(self) -> str:
        return "Hermes"

    @property
    def description(self) -> str:
        return (
            "A helpful AI assistant trained by Nous Research. "
            "Specializes in instruction following and helpful responses."
        )

    def build_system_prompt(self, context: dict | None = None) -> str:
        """Build Hermes-specific system prompt."""
        base = (
            "You are Hermes, a helpful AI assistant trained by Nous Research. "
            "You excel at following instructions and providing clear, accurate responses. "
            "Be concise and direct in your answers."
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
        """Execute task with Hermes."""
        system_prompt = self.build_system_prompt(context)
        return provider.complete(
            prompt=task,
            system_prompt=system_prompt,
        )


def get_hermes_adapter() -> HermesAdapter:
    """Get Hermes adapter instance."""
    return HermesAdapter()