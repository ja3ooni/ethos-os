"""OpenAI provider - GPT-4, GPT-4o, GPT-3.5-turbo."""

from typing import AsyncGenerator

from openai import AsyncOpenAI

from ethos_os.llm.base import (
    LLMProvider,
    LLMResponse,
    LLMStreamChunk,
    EmbeddingResponse,
)
from ethos_os.llm.config import get_llm_config


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""

    def __init__(self, config: dict | None = None):
        self._config = config or {}
        self._llm_config = get_llm_config()
        self._api_key = self._config.get(
            "api_key",
            self._llm_config.openai_api_key
        )
        self._model = self._config.get(
            "model",
            self._llm_config.openai_model
        )
        self._client = None

    @property
    def provider_type(self) -> str:
        return "openai"

    @property
    def model(self) -> str:
        return self._model

    @property
    def _openai_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=self._api_key,
            )
        return self._client

    def _build_messages(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> list[dict]:
        """Build messages array."""
        messages = []
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        messages.append({
            "role": "user",
            "content": prompt
        })
        return messages

    def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        context: dict | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Generate completion (sync wrapper for async)."""
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            return loop.run_until_complete(
                self._complete_async(
                    prompt, system_prompt, context, temperature, max_tokens
                )
            )
        except RuntimeError:
            return asyncio.run(
                self._complete_async(
                    prompt, system_prompt, context, temperature, max_tokens
                )
            )

    async def _complete_async(
        self,
        prompt: str,
        system_prompt: str | None = None,
        context: dict | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Generate completion async."""
        messages = self._build_messages(prompt, system_prompt)

        kwargs = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
        }

        if max_tokens:
            kwargs["max_tokens"] = max_tokens

        response = await self._openai_client.chat.completions.create(
            **kwargs
        )

        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            model=self._model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            finish_reason=choice.finish_reason,
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
            "temperature": temperature,
            "stream": True,
        }

        if max_tokens:
            kwargs["max_tokens"] = max_tokens

        stream = await self._openai_client.chat.completions.create(**kwargs)

        async for chunk in stream:
            choice = chunk.choices[0]
            if choice.delta.content:
                yield LLMStreamChunk(
                    delta=choice.delta.content,
                    model=self._model,
                    finish_reason=choice.finish_reason,
                )

    def embed(self, text: str) -> EmbeddingResponse:
        """Generate embedding."""
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            return loop.run_until_complete(self._embed_async(text))
        except RuntimeError:
            return asyncio.run(self._embed_async(text))

    async def _embed_async(self, text: str) -> EmbeddingResponse:
        """Generate embedding async."""
        response = await self._openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )

        return EmbeddingResponse(
            embedding=response.data[0].embedding,
            model="text-embedding-3-small",
            tokens=response.usage.total_tokens,
        )

    def is_available(self) -> bool:
        """Check if OpenAI is available."""
        return bool(self._api_key)


def get_openai_provider() -> OpenAIProvider:
    """Get OpenAI provider instance."""
    return OpenAIProvider()