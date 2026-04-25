"""Anthropic provider - Claude 3.5 Sonnet, Claude 3 Opus."""

from typing import AsyncGenerator

import anthropic

from ethos_os.llm.base import (
    LLMProvider,
    LLMResponse,
    LLMStreamChunk,
    EmbeddingResponse,
)
from ethos_os.llm.config import get_llm_config


class AnthropicProvider(LLMProvider):
    """Anthropic LLM provider."""

    def __init__(self, config: dict | None = None):
        self._config = config or {}
        self._llm_config = get_llm_config()
        self._api_key = self._config.get(
            "api_key",
            self._llm_config.anthropic_api_key
        )
        self._model = self._config.get(
            "model",
            self._llm_config.anthropic_model
        )
        self._client = None

    @property
    def provider_type(self) -> str:
        return "anthropic"

    @property
    def model(self) -> str:
        return self._model

    @property
    def _anthropic_client(self) -> anthropic.AsyncAnthropic:
        if self._client is None:
            self._client = anthropic.AsyncAnthropic(
                api_key=self._api_key,
            )
        return self._client

    def _build_messages(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> list[dict]:
        """Build messages array."""
        if system_prompt:
            return [
                {
                    "role": "user",
                    "content": f"{system_prompt}\n\n{prompt}"
                }
            ]
        return [
            {
                "role": "user",
                "content": prompt
            }
        ]

    def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        context: dict | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Generate completion."""
        messages = self._build_messages(prompt, system_prompt)

        kwargs = {
            "model": self._model,
            "messages": messages,
            "max_tokens": max_tokens or 4096,
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        if temperature:
            kwargs["temperature"] = temperature

        import asyncio
        try:
            loop = asyncio.get_running_loop()
            return loop.run_until_complete(
                self._complete_async(**kwargs)
            )
        except RuntimeError:
            return asyncio.run(self._complete_async(**kwargs))

    async def _complete_async(
        self,
        model: str,
        messages: list[dict],
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Generate completion async."""
        response = await self._anthropic_client.messages.create(
            model=model,
            messages=messages,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        content = response.content[0].text if response.content else ""
        return LLMResponse(
            content=content,
            model=self._model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            finish_reason=response.stop_reason,
        )

    async def complete_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        context: dict | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncGenerator[LLMStreamChunk, None]:
        """Generate streaming completion."""
        messages = self._build_messages(prompt, system_prompt)

        kwargs = {
            "model": self._model,
            "messages": messages,
            "max_tokens": max_tokens or 4096,
            "stream": True,
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        if temperature:
            kwargs["temperature"] = temperature

        async with self._anthropic_client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                if text:
                    yield LLMStreamChunk(
                        delta=text,
                        model=self._model,
                        finish_reason=None,
                    )

    def embed(self, text: str) -> EmbeddingResponse:
        """Claude doesn't have embeddings API."""
        raise NotImplementedError(
            "Anthropic does not provide embeddings API. "
            "Use OpenAI or Ollama for embeddings."
        )

    def is_available(self) -> bool:
        """Check if Anthropic is available."""
        return bool(self._api_key)


def get_anthropic_provider() -> AnthropicProvider:
    """Get Anthropic provider instance."""
    return AnthropicProvider()