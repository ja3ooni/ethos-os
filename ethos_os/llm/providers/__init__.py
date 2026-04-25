"""LLM Providers.

Available:
- ollama: Local Llama3, Mistral (default for v0.2)
- openai: GPT-4, GPT-4o, GPT-3.5-turbo
- anthropic: Claude 3.5 Sonnet, Claude 3 Opus
- azure: Azure OpenAI (enterprise)
"""

from ethos_os.llm.base import (
    LLMProvider,
    ProviderRegistry,
    get_provider_registry,
    get_default_provider,
    set_default_provider,
)
from ethos_os.llm.config import (
    LLMConfig,
    LLMProviderType,
    get_llm_config,
)
from ethos_os.llm.providers.ollama import OllamaProvider, get_ollama_provider
from ethos_os.llm.providers.openai import OpenAIProvider, get_openai_provider
from ethos_os.llm.providers.anthropic import (
    AnthropicProvider,
    get_anthropic_provider,
)
from ethos_os.llm.providers.azure import AzureProvider, get_azure_provider

__all__ = [
    "LLMProvider",
    "ProviderRegistry",
    "get_provider_registry",
    "get_default_provider",
    "set_default_provider",
    "LLMConfig",
    "LLMProviderType",
    "get_llm_config",
    "OllamaProvider",
    "get_ollama_provider",
    "OpenAIProvider",
    "get_openai_provider",
    "AnthropicProvider",
    "get_anthropic_provider",
    "AzureProvider",
    "get_azure_provider",
]