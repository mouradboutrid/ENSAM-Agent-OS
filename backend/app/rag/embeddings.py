from __future__ import annotations
from typing import Optional

from app.core.llm import OllamaClient


class EmbeddingGenerator:
    def __init__(self, ollama_client: OllamaClient):
        self._client = ollama_client
        self._cache: dict[str, list[float]] = {}

    async def embed_single(self, text: str, use_cache: bool = True) -> list[float]:
        if use_cache and text in self._cache:
            return self._cache[text]
        results = await self._client.embed([text])
        embedding = results[0]
        if use_cache:
            self._cache[text] = embedding
        return embedding

    async def embed_batch(self, texts: list[str], use_cache: bool = True) -> list[list[float]]:
        results = []
        to_compute = []
        indices = []
        for i, text in enumerate(texts):
            if use_cache and text in self._cache:
                results.append(self._cache[text])
            else:
                results.append(None)
                to_compute.append(text)
                indices.append(i)
        if to_compute:
            computed = await self._client.embed(to_compute)
            for idx, embedding in zip(indices, computed):
                results[idx] = embedding
                if use_cache:
                    self._cache[to_compute[indices.index(idx)]] = embedding
        return results

    def clear_cache(self):
        self._cache.clear()

    @property
    def cache_size(self) -> int:
        return len(self._cache)
