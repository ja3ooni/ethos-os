"""Azure OpenAI provider - Enterprise option."""

from typing import AsyncGenerator

from openai import AsyncAzureOpenAI

from ethos_os.llm.base import (
    LLMProvider,
    LLMResponse,
    LLMStreamChunk,
    EmbeddingResponse,
)
from ethos_os.llm.config import get_llm_config


class AzureProvider(LLMProvider):
    """Azure OpenAI LLM provider."""

    def __init__(self, config: dict | None = None):
        self._config = config or {}
        self._llm_config = get_llm_config()
        self._api_key = self._config.get(
            "api_key",
            self._llm_config.azure_api_key
        )
        self._endpoint = self._config.get(
            "endpoint",
            self._llm_config.azure_endpoint
        )
        self._deployment = self._config.get(
            "deployment",
            self._llm_config.azure_deployment
        )
        self._api_version = self._config.get(
            "api_version",
            self._llm_config.azure_api_version
        )
        self._client = None

    @property
    def provider_type(self) -> str:
        return "azure"

    @property
    def model(self) -> str:
        return self._deployment

    @property
    def _azure_client(self) -> AsyncAzureOpenAI:
        if self._client is None:
            self._client = AsyncAzureOpenAI(
                api_key=self._api_key,
                api_version=self._api_version,
                azure_endpoint=self._endpoint,
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
        """Generate completion."""
        messages = self._build_messages(prompt, system_prompt)

        import asyncio
        try:
            loop = asyncio.get_running_loop()
            return loop.run_until_complete(
                self._complete_async(
                    messages, temperature, max_tokens
                )
            )
        except RuntimeError:
            return asyncio.run(
                self._complete_async(
                    messages, temperature, max_tokens
                )
            )

    async def _complete_async(
        self,
        messages: list[dict],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Generate completion async."""
        response = await self._azure_client.chat.completions.create(
            model=self._deployment,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            model=self._deployment,
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

        stream = await self._azure_client.chat.completions.create(
            model=self._deployment,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        async for chunk in stream:
            choice = chunk.choices[0]
            if choice.delta.content:
                yield LLMStreamChunk(
                    delta=choice.delta.content,
                    model=self._deployment,
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
        response = await self._azure_client.embeddings.create(
            model=self._deployment,
            input=text,
        )

        return EmbeddingResponse(
            embedding=response.data[0].embedding,
            model=self._deployment,
        )

    def is_available(self) -> bool:
        """Check if Azure is available."""
        return bool(self._api_key and self._endpoint and self._deployment)


def get_azure_provider() -> AzureProvider:
    """Get Azure provider instance."""
    return AzureProvider()