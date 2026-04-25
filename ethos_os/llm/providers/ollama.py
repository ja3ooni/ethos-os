"""Ollama provider - local LLM for privacy/cost efficiency.

Key benefits:
- Local: No API cost
- Private: Data stays on machine
- Fast: Sub-second latency (after model loaded)
"""

import json
from typing import AsyncGenerator

import httpx

from ethos_os.llm.base import (
    LLMProvider,
    LLMResponse,
    LLMStreamChunk,
    EmbeddingResponse,
)
from ethos_os.llm.config import get_llm_config


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""

    def __init__(self, config: dict | None = None):
        self._config = config or {}
        self._llm_config = get_llm_config()
        self._base_url = self._config.get(
            "base_url",
            self._llm_config.ollama_base_url
        )
        self._model = self._config.get(
            "model",
            self._llm_config.ollama_model
        )
        self._temperature = self._config.get(
            "temperature",
            self._llm_config.ollama_temperature
        )

    @property
    def provider_type(self) -> str:
        return "ollama"

    @property
    def model(self) -> str:
        return self._model

    def _build_messages(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> list[dict]:
        """Build messages array for Ollama."""
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

        payload = {
            "model": self._model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature or self._temperature,
            }
        }

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        # Context injection
        if context:
            payload["context"] = context

        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(
                    f"{self._base_url}/api/chat",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

                return LLMResponse(
                    content=data["message"]["content"],
                    model=self._model,
                    usage=data.get("done_reason"),
                    finish_reason=data.get("done_reason"),
                )
        except httpx.ConnectError:
            return LLMResponse(
                content="[Ollama not connected. Start with: ollama serve]",
                model=self._model,
                finish_reason="error",
            )
        except httpx.HTTPStatusError as e:
            return LLMResponse(
                content=f"[Ollama error: {e.response.status_code}]",
                model=self._model,
                finish_reason="error",
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

        payload = {
            "model": self._model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature or self._temperature,
            }
        }

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                async with client.stream(
                    "POST",
                    f"{self._base_url}/api/chat",
                    json=payload
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            data = json.loads(line)
                            if "message" in data:
                                yield LLMStreamChunk(
                                    delta=data["message"].get("content", ""),
                                    model=self._model,
                                    finish_reason=data.get("done_reason"),
                                )
            except httpx.ConnectError:
                yield LLMStreamChunk(
                    delta="[Ollama not connected]",
                    model=self._model,
                    finish_reason="error",
                )

    def embed(self, text: str) -> EmbeddingResponse:
        """Generate embedding.

        Note: Ollama requires separate embedding model.
        Default: nomic-embed-text
        """
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{self._base_url}/api/embeddings",
                json={
                    "model": self._model,
                    "prompt": text,
                }
            )
            response.raise_for_status()
            data = response.json()

            return EmbeddingResponse(
                embedding=data["embedding"],
                model=self._model,
            )

    def is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self._base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False


def get_ollama_provider() -> OllamaProvider:
    """Get Ollama provider instance."""
    return OllamaProvider()