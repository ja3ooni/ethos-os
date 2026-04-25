"""LLM Configuration for EthosOS.

Supports:
- OpenAI (GPT-4, GPT-4o, GPT-3.5-turbo)
- Anthropic (Claude 3.5 Sonnet, Claude 3 Opus)
- Ollama (local Llama3, Mistral)
- Azure OpenAI (enterprise)
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProviderType:
    """Provider type constants."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    AZURE = "azure"


class LLMConfig(BaseSettings):
    """LLM provider configuration."""

    provider: str = Field(
        default=LLMProviderType.OLLAMA,
        description="Active LLM provider (openai, anthropic, ollama, azure)"
    )

    # OpenAI
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key"
    )
    openai_model: str = Field(
        default="gpt-4o",
        description="OpenAI model to use"
    )

    # Anthropic
    anthropic_api_key: str = Field(
        default="",
        description="Anthropic API key"
    )
    anthropic_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Anthropic model to use"
    )

    # Ollama (local)
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama server URL"
    )
    ollama_model: str = Field(
        default="llama3",
        description="Ollama model to use"
    )
    ollama_temperature: float = Field(
        default=0.7,
        description="Ollama temperature"
    )

    # Azure OpenAI
    azure_api_key: str = Field(
        default="",
        description="Azure OpenAI API key"
    )
    azure_endpoint: str = Field(
        default="",
        description="Azure OpenAI endpoint"
    )
    azure_deployment: str = Field(
        default="",
        description="Azure deployment name"
    )
    azure_api_version: str = Field(
        default="2024-02-01",
        description="Azure API version"
    )

    # Token efficiency
    max_tokens: int = Field(
        default=4096,
        description="Max tokens to generate"
    )
    enable_streaming: bool = Field(
        default=True,
        description="Enable streaming responses"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache
def get_llm_config() -> LLMConfig:
    """Get cached LLM config."""
    return LLMConfig()