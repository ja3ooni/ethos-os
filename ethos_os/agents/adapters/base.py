"""Agent adapter base interface.

Wraps LLM calls with agent-specific prompt engineering.
"""

from abc import ABC, abstractmethod

from ethos_os.llm.base import LLMProvider, LLMResponse


class AgentAdapter(ABC):
    """Base agent adapter.

    Implementations wrap LLM calls with agent-specific prompts.
    """

    @property
    @abstractmethod
    def adapter_type(self) -> str:
        """Return adapter type identifier."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return agent name."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Return agent description."""
        pass

    def build_system_prompt(self, context: dict | None = None) -> str:
        """Build system prompt from context.

        Override in subclasses for agent-specific prompts.
        """
        base = f"You are {self.name}. {self.description}"
        if context:
            context_info = self._format_context(context)
            return f"{base}\n\nContext:\n{context_info}"
        return base

    def _format_context(self, context: dict) -> str:
        """Format context for prompt."""
        lines = []
        for key, value in context.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)

    @abstractmethod
    def execute(
        self,
        task: str,
        provider: LLMProvider,
        context: dict | None = None,
    ) -> LLMResponse:
        """Execute task with LLM provider.

        Args:
            task: Task description
            provider: LLM provider
            context: Optional context

        Returns:
            LLMResponse with agent response
        """
        pass


class AdapterRegistry:
    """Registry for agent adapters."""

    def __init__(self):
        self._adapters: dict[str, AgentAdapter] = {}

    def register(self, adapter_type: str, adapter: AgentAdapter) -> None:
        """Register an adapter."""
        self._adapters[adapter_type] = adapter

    def get(self, adapter_type: str) -> AgentAdapter:
        """Get adapter by type."""
        if adapter_type not in self._adapters:
            raise ValueError(f"Unknown adapter: {adapter_type}")
        return self._adapters[adapter_type]

    def list_adapters(self) -> list[str]:
        """List available adapters."""
        return list(self._adapters.keys())


# Global registry
_adapter_registry = AdapterRegistry()


def get_adapter_registry() -> AdapterRegistry:
    """Get adapter registry."""
    return _adapter_registry


def get_default_adapter() -> AgentAdapter:
    """Get default adapter."""
    return _adapter_registry.get("general")