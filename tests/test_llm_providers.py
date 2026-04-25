"""Tests for LLM provider integration."""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from ethos_os.llm.base import (
    LLMProvider,
    LLMResponse,
    LLMStreamChunk,
    EmbeddingResponse,
    ProviderRegistry,
)
from ethos_os.llm.config import (
    LLMConfig,
    LLMProviderType,
)
from ethos_os.llm.providers.ollama import OllamaProvider
from ethos_os.llm.providers.openai import OpenAIProvider
from ethos_os.llm.providers.anthropic import AnthropicProvider
from ethos_os.llm.providers.azure import AzureProvider


class TestProviderRegistry:
    """Test ProviderRegistry."""

    def test_register_and_get(self):
        """Test registration and retrieval."""
        registry = ProviderRegistry()
        mock_provider = Mock(spec=LLMProvider)
        mock_provider.provider_type = "test"
        mock_provider.model = "test-model"

        registry.register("test", mock_provider)
        provider = registry.get("test")
        assert provider == mock_provider

    def test_default_provider(self):
        """Test default provider."""
        registry = ProviderRegistry()
        mock_provider = Mock(spec=LLMProvider)
        mock_provider.provider_type = "test"
        mock_provider.model = "test-model"

        registry.register("test", mock_provider)
        registry.set_default("test")
        provider = registry.get()
        assert provider == mock_provider

    def test_list_providers(self):
        """Test listing providers."""
        registry = ProviderRegistry()
        mock1 = Mock(spec=LLMProvider)
        mock1.provider_type = "test1"
        mock1.model = "model1"
        mock2 = Mock(spec=LLMProvider)
        mock2.provider_type = "test2"
        mock2.model = "model2"

        registry.register("test1", mock1)
        registry.register("test2", mock2)

        providers = registry.list_providers()
        assert "test1" in providers
        assert "test2" in providers


class TestOllamaProvider:
    """Test Ollama provider."""

    def test_init(self):
        """Test initialization."""
        provider = OllamaProvider()
        assert provider.provider_type == "ollama"

    def test_model_default(self):
        """Test default model."""
        provider = OllamaProvider()
        assert provider.model == "llama3"

    def test_model_from_config(self):
        """Test model from config."""
        provider = OllamaProvider({"model": "mistral"})
        assert provider.model == "mistral"

    def test_build_messages(self):
        """Test message building."""
        provider = OllamaProvider()
        messages = provider._build_messages("Hello", "System prompt")
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "System prompt"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Hello"

    def test_build_messages_no_system(self):
        """Test message building without system."""
        provider = OllamaProvider()
        messages = provider._build_messages("Hello")
        assert len(messages) == 1
        assert messages[0]["role"] == "user"

    @patch("ethos_os.llm.providers.ollama.httpx.Client")
    def test_complete(self, mock_client_class):
        """Test completion."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "message": {"content": "Test response"},
            "done_reason": "stop",
        }
        mock_client = Mock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        provider = OllamaProvider()
        response = provider.complete("Test prompt")

        assert response.content == "Test response"
        assert response.model == "llama3"

    pass


class TestOpenAIProvider:
    """Test OpenAI provider."""

    def test_init(self):
        """Test initialization."""
        provider = OpenAIProvider({"api_key": "sk-test"})
        assert provider.provider_type == "openai"

    def test_model_default(self):
        """Test default model."""
        provider = OpenAIProvider({"api_key": "sk-test"})
        assert provider.model == "gpt-4o"

    def test_build_messages(self):
        """Test message building."""
        provider = OpenAIProvider()
        messages = provider._build_messages("Hello", "System")
        assert len(messages) == 2
        assert messages[0]["role"] == "system"


class TestAnthropicProvider:
    """Test Anthropic provider."""

    def test_init(self):
        """Test initialization."""
        provider = AnthropicProvider({"api_key": "sk-ant-test"})
        assert provider.provider_type == "anthropic"

    def test_model_default(self):
        """Test default model."""
        provider = AnthropicProvider({"api_key": "sk-ant-test"})
        assert "claude" in provider.model


class TestAzureProvider:
    """Test Azure provider."""

    def test_init(self):
        """Test initialization."""
        provider = AzureProvider({
            "api_key": "test-key",
            "endpoint": "https://test.openai.azure.com",
            "deployment": "test-deployment",
        })
        assert provider.provider_type == "azure"

    def test_is_available_full_config(self):
        """Test availability with full config."""
        provider = AzureProvider({
            "api_key": "test-key",
            "endpoint": "https://test.openai.azure.com",
            "deployment": "test-deployment",
        })
        assert provider.is_available() is True

    def test_is_available_missing_config(self):
        """Test availability with missing config."""
        provider = AzureProvider()
        assert provider.is_available() is False


class TestLLMConfig:
    """Test LLM configuration."""

    def test_defaults(self):
        """Test default config."""
        config = LLMConfig()
        assert config.provider == "ollama"

    def test_ollama_defaults(self):
        """Test Ollama defaults."""
        config = LLMConfig()
        assert config.ollama_base_url == "http://localhost:11434"
        assert config.ollama_model == "llama3"

    def test_openai_defaults(self):
        """Test OpenAI defaults."""
        config = LLMConfig()
        assert config.openai_model == "gpt-4o"

    def test_anthropic_defaults(self):
        """Test Anthropic defaults."""
        config = LLMConfig()
        assert "claude" in config.anthropic_model

    def test_settings_from_env(self):
        """Test settings from environment."""
        config = LLMConfig(provider="openai")
        assert config.provider == "openai"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])