"""LLM Provider base interface.

Token-efficient architecture:
1. Provider-agnostic: Abstract provider behind interface
2. Streaming: Support streaming responses
3. Caching: Cache embeddings and common completions
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator


class LLMResponse:
    """LLM response wrapper."""

    def __init__(
        self,
        content: str,
        model: str,
        usage: dict | None = None,
        finish_reason: str | None = None,
    ):
        self.content = content
        self.model = model
        self.usage = usage or {}
        self.finish_reason = finish_reason


class LLMStreamChunk:
    """Streaming chunk from LLM."""

    def __init__(
        self,
        delta: str,
        model: str,
        finish_reason: str | None = None,
    ):
        self.delta = delta
        self.model = model
        self.finish_reason = finish_reason


class EmbeddingResponse:
    """Embedding response wrapper."""

    def __init__(
        self,
        embedding: list[float],
        model: str,
        tokens: int | None = None,
    ):
        self.embedding = embedding
        self.model = model
        self.tokens = tokens


class LLMProvider(ABC):
    """Base LLM provider interface.

    Implementations must provide:
    - complete(): Generate completion
    - complete_stream(): Streaming completion
    - embed(): Generate embeddings
    """

    @property
    @abstractmethod
    def provider_type(self) -> str:
        """Return provider type identifier."""
        pass

    @property
    @abstractmethod
    def model(self) -> str:
        """Return model name."""
        pass

    @abstractmethod
    def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        context: dict | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Generate completion.

        Args:
            prompt: User prompt
            system_prompt: System prompt
            context: Additional context
            temperature: Sampling temperature
            max_tokens: Max tokens to generate

        Returns:
            LLMResponse with content
        """
        pass

    @abstractmethod
    async def complete_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        context: dict | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncGenerator[LLMStreamChunk, None]:
        """Generate streaming completion.

        Yields chunks as they arrive.
        """
        pass

    @abstractmethod
    def embed(self, text: str) -> EmbeddingResponse:
        """Generate embedding for text.

        Args:
            text: Text to embed

        Returns:
            EmbeddingResponse with embedding vector
        """
        pass

    def is_available(self) -> bool:
        """Check if provider is available."""
        return True


class ProviderRegistry:
    """Registry for LLM providers."""

    def __init__(self):
        self._providers: dict[str, LLMProvider] = {}
        self._default: str | None = None

    def register(self, provider_type: str, provider: LLMProvider) -> None:
        """Register a provider."""
        self._providers[provider_type] = provider

    def get(self, provider_type: str | None = None) -> LLMProvider:
        """Get provider by type."""
        if provider_type is None:
            provider_type = self._default
        if provider_type is None:
            raise ValueError("No provider registered")
        if provider_type not in self._providers:
            raise ValueError(f"Unknown provider: {provider_type}")
        return self._providers[provider_type]

    def set_default(self, provider_type: str) -> None:
        """Set default provider."""
        self._default = provider_type

    def list_providers(self) -> list[str]:
        """List available providers."""
        return list(self._providers.keys())


# Global registry
_provider_registry = ProviderRegistry()


def get_provider_registry() -> ProviderRegistry:
    """Get provider registry."""
    return _provider_registry


def get_default_provider() -> LLMProvider:
    """Get default provider from registry."""
    return _provider_registry.get()


def set_default_provider(provider_type: str) -> None:
    """Set default provider type."""
    _provider_registry.set_default(provider_type)