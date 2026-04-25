"""Agent Adapters.

Wrappers around LLM calls with agent-specific prompt engineering.

Available adapters:
- hermes: NousResearch's Hermes (via Ollama or API)
- pi: Inflection AI's Pi (via compatible LLM)
- general: General-purpose fallback
"""

from ethos_os.agents.adapters.base import (
    AgentAdapter,
    AdapterRegistry,
    get_adapter_registry,
    get_default_adapter,
)
from ethos_os.agents.adapters.hermes import HermesAdapter, get_hermes_adapter
from ethos_os.agents.adapters.pi import PiAdapter, get_pi_adapter
from ethos_os.agents.adapters.general import GeneralAgentAdapter, get_general_adapter

# Initialize registry
_registry = get_adapter_registry()
_registry.register("hermes", get_hermes_adapter())
_registry.register("pi", get_pi_adapter())
_registry.register("general", get_general_adapter())

__all__ = [
    "AgentAdapter",
    "AdapterRegistry",
    "get_adapter_registry",
    "get_default_adapter",
    "HermesAdapter",
    "get_hermes_adapter",
    "PiAdapter",
    "get_pi_adapter",
    "GeneralAgentAdapter",
    "get_general_adapter",
]