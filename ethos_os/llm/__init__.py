"""LLM module for EthosOS.

Multi-provider LLM support with token-efficient architecture.

Providers:
- ollama: Local Llama3, Mistral (default for v0.2)
- openai: GPT-4, GPT-4o, GPT-3.5-turbo
- anthropic: Claude 3.5 Sonnet, Claude 3 Opus
- azure: Azure OpenAI (enterprise)

Configuration:
Set LLM_PROVIDER in .env:
- ollama (default): Local, no API cost
- openai: OpenAI API
- anthropic: Anthropic API
- azure: Azure OpenAI

Token Efficiency Principles:
1. Provider-agnostic: Abstract provider behind interface
2. Local-first: Prefer Ollama for cost/privacy
3. Streaming: Stream responses, don't wait for full completion
4. Caching: Cache embeddings and common completions
"""

from ethos_os.llm.base import (
    LLMProvider,
    LLMResponse,
    LLMStreamChunk,
    EmbeddingResponse,
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
from ethos_os.llm.providers import (
    OllamaProvider,
    OpenAIProvider,
    AnthropicProvider,
    AzureProvider,
    get_ollama_provider,
    get_openai_provider,
    get_anthropic_provider,
    get_azure_provider,
)

# Initialize registry with providers
_registry = get_provider_registry()

# Register all providers
_registry.register("ollama", get_ollama_provider())
_registry.register("openai", get_openai_provider())
_registry.register("anthropic", get_anthropic_provider())
_registry.register("azure", get_azure_provider())

# Set default from config
_config = get_llm_config()
_registry.set_default(_config.provider)

__all__ = [
    # Base
    "LLMProvider",
    "LLMResponse",
    "LLMStreamChunk",
    "EmbeddingResponse",
    "ProviderRegistry",
    "get_provider_registry",
    "get_default_provider",
    "set_default_provider",
    # Config
    "LLMConfig",
    "LLMProviderType",
    "get_llm_config",
    # Providers
    "OllamaProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "AzureProvider",
    "get_ollama_provider",
    "get_openai_provider",
    "get_anthropic_provider",
    "get_azure_provider",
]