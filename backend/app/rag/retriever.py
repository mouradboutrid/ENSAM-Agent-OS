from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from app.memory.semantic import SemanticMemory
from app.rag.embeddings import EmbeddingGenerator


@dataclass
class RetrievalResult:
    text: str
    score: float
    metadata: dict = field(default_factory=dict)
    doc_id: str = ""


class SemanticRetriever:
    def __init__(self, semantic_memory: SemanticMemory, embedding_generator: EmbeddingGenerator):
        self._memory = semantic_memory
        self._embedder = embedding_generator

    async def retrieve(
        self, query: str, n_results: int = 5, where: Optional[dict] = None, score_threshold: float = 0.0,
    ) -> list[RetrievalResult]:
        query_embedding = await self._embedder.embed_single(query)
        raw = self._memory.search_documents(query_embedding, n_results=n_results, where=where)
        results = []
        if raw and raw.get("documents") and raw["documents"][0]:
            for i, doc in enumerate(raw["documents"][0]):
                distance = raw["distances"][0][i] if raw.get("distances") else 0
                score = 1.0 - distance
                if score < score_threshold:
                    continue
                results.append(RetrievalResult(
                    text=doc,
                    score=score,
                    metadata=raw["metadatas"][0][i] if raw.get("metadatas") else {},
                    doc_id=raw["ids"][0][i] if raw.get("ids") else "",
                ))
        results.sort(key=lambda r: r.score, reverse=True)
        return results

    async def retrieve_with_context(
        self, query: str, n_results: int = 5, context_template: str = "Source [{i}] (score: {score:.2f}): {text}",
    ) -> tuple[list[RetrievalResult], str]:
        results = await self.retrieve(query, n_results)
        context_parts = []
        for i, r in enumerate(results):
            context_parts.append(context_template.format(i=i + 1, score=r.score, text=r.text))
        context = "\n\n".join(context_parts)
        return results, context
