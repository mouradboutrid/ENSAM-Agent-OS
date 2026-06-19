from __future__ import annotations
import asyncio
import time
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, Any, Optional

import httpx
from groq import AsyncGroq


@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    metadata: dict = field(default_factory=dict)


class BaseLLMClient(ABC):
    @abstractmethod
    async def generate(self, messages: list[dict], **kwargs) -> LLMResponse: ...

    @abstractmethod
    async def stream(self, messages: list[dict], **kwargs) -> AsyncIterator[str]: ...

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]: ...

    @abstractmethod
    async def health_check(self) -> bool: ...

    @abstractmethod
    async def close(self) -> None: ...


class OllamaClient(BaseLLMClient):
    def __init__(self, base_url: str, model: str, timeout: float = 600.0):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=timeout)

    async def generate(self, messages: list[dict], **kwargs) -> LLMResponse:
        start = time.perf_counter()
        payload = {"model": self.model, "messages": messages, "stream": False}
        payload.update(kwargs)
        resp = await self.client.post("/api/chat", json=payload)
        resp.raise_for_status()
        data = resp.json()
        elapsed = (time.perf_counter() - start) * 1000
        return LLMResponse(
            content=data["message"]["content"],
            model=self.model,
            provider="ollama",
            input_tokens=data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
            latency_ms=elapsed,
            cost_usd=0.0,
            metadata={"total_duration": data.get("total_duration", 0)},
        )

    async def stream(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        payload = {"model": self.model, "messages": messages, "stream": True}
        payload.update(kwargs)
        async with self.client.stream("POST", "/api/chat", json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line:
                    chunk = json.loads(line)
                    if chunk.get("message", {}).get("content"):
                        yield chunk["message"]["content"]

    async def embed(self, texts: list[str]) -> list[list[float]]:
        results = []
        for text in texts:
            resp = await self.client.post(
                "/api/embed", json={"model": self.model, "input": text}
            )
            resp.raise_for_status()
            data = resp.json()
            results.append(data["embeddings"][0])
        return results

    async def health_check(self) -> bool:
        try:
            resp = await self.client.get("/api/tags")
            return resp.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        await self.client.aclose()


class GroqClient(BaseLLMClient):
    def __init__(
        self,
        api_key: str,
        model: str,
        cost_input: float = 0.00059,
        cost_output: float = 0.00079,
        max_retries: int = 3,
    ):
        self.model = model
        self.client = AsyncGroq(api_key=api_key)
        self.cost_input = cost_input
        self.cost_output = cost_output
        self.max_retries = max_retries

    async def generate(self, messages: list[dict], **kwargs) -> LLMResponse:
        start = time.perf_counter()
        last_err = None
        for attempt in range(self.max_retries):
            try:
                resp = await self.client.chat.completions.create(
                    model=self.model, messages=messages, **kwargs
                )
                elapsed = (time.perf_counter() - start) * 1000
                usage = resp.usage
                cost = (
                    usage.prompt_tokens / 1000 * self.cost_input
                    + usage.completion_tokens / 1000 * self.cost_output
                )
                return LLMResponse(
                    content=resp.choices[0].message.content or "",
                    model=self.model,
                    provider="groq",
                    input_tokens=usage.prompt_tokens,
                    output_tokens=usage.completion_tokens,
                    latency_ms=elapsed,
                    cost_usd=cost,
                    metadata={"finish_reason": resp.choices[0].finish_reason},
                )
            except Exception as e:
                last_err = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2**attempt)
        raise last_err

    async def stream(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        stream_resp = await self.client.chat.completions.create(
            model=self.model, messages=messages, stream=True, **kwargs
        )
        async for chunk in stream_resp:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("Groq does not support embeddings")

    async def health_check(self) -> bool:
        try:
            resp = await self.client.models.list()
            return True
        except Exception:
            return False

    async def close(self) -> None:
        await self.client.close()


class LLMManager:
    def __init__(self, ollama: OllamaClient, groq: GroqClient):
        self.ollama = ollama
        self.groq = groq

    async def generate(
        self, messages: list[dict], provider: str = "groq", **kwargs
    ) -> LLMResponse:
        # Cloud-first: try Groq, fallback to Ollama
        if provider == "groq":
            try:
                return await self.groq.generate(messages, **kwargs)
            except Exception as groq_err:
                try:
                    return await self.ollama.generate(messages, **kwargs)
                except Exception:
                    raise groq_err

        # Local-first: try Ollama, fallback to Groq
        try:
            return await self.ollama.generate(messages, **kwargs)
        except Exception as ollama_err:
            try:
                return await self.groq.generate(messages, **kwargs)
            except Exception:
                raise ollama_err

    async def stream(
        self, messages: list[dict], provider: str = "groq", **kwargs
    ) -> AsyncIterator[str]:
        if provider == "groq":
            try:
                async for token in self.groq.stream(messages, **kwargs):
                    yield token
                return
            except Exception:
                pass
            async for token in self.ollama.stream(messages, **kwargs):
                yield token
        else:
            try:
                async for token in self.ollama.stream(messages, **kwargs):
                    yield token
                return
            except Exception:
                pass
            async for token in self.groq.stream(messages, **kwargs):
                yield token

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return await self.ollama.embed(texts)

    async def close(self):
        await self.ollama.close()
        await self.groq.close()

