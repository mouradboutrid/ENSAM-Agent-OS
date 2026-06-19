from __future__ import annotations
import uuid
import asyncio
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable, Optional

from app.rag.ingestion import FileParser, TextChunker, ParsedDocument, DocumentChunk
from app.rag.embeddings import EmbeddingGenerator
from app.rag.retriever import SemanticRetriever, RetrievalResult
from app.memory.semantic import SemanticMemory
from app.core.llm import LLMManager


@dataclass
class IngestionProgress:
    task_id: str
    filename: str
    status: str = "pending"
    total_chunks: int = 0
    processed_chunks: int = 0
    phase: str = "parsing"
    error: Optional[str] = None


@dataclass
class RAGResponse:
    answer: str
    sources: list[RetrievalResult] = field(default_factory=list)
    model: str = ""
    provider: str = ""
    latency_ms: float = 0.0
    cost_usd: float = 0.0


class RAGPipeline:
    def __init__(
        self,
        semantic_memory: SemanticMemory,
        embedding_generator: EmbeddingGenerator,
        llm_manager: LLMManager,
        graph_memory: Optional[Any] = None,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
    ):
        self._memory = semantic_memory
        self._embedder = embedding_generator
        self._llm = llm_manager
        self._graph = graph_memory
        self._chunker = TextChunker(chunk_size, chunk_overlap)
        self._retriever = SemanticRetriever(semantic_memory, embedding_generator)
        self._ingestion_tasks: dict[str, IngestionProgress] = {}

    async def ingest_file(
        self, file_path: str, content_bytes: Optional[bytes] = None,
        metadata: Optional[dict] = None, progress_callback: Optional[Callable] = None,
    ) -> IngestionProgress:
        task_id = str(uuid.uuid4())
        progress = IngestionProgress(task_id=task_id, filename=file_path)
        self._ingestion_tasks[task_id] = progress

        try:
            progress.phase = "parsing"
            if progress_callback:
                await progress_callback(progress)
            doc = FileParser.parse(file_path, content_bytes)
            if metadata:
                doc.metadata.update(metadata)

            progress.phase = "chunking"
            if progress_callback:
                await progress_callback(progress)
            chunks = self._chunker.chunk(doc)
            progress.total_chunks = len(chunks)

            progress.phase = "embedding"
            if progress_callback:
                await progress_callback(progress)
            texts = [c.text for c in chunks]
            embeddings = await self._embedder.embed_batch(texts, use_cache=False)

            progress.phase = "storing"
            if progress_callback:
                await progress_callback(progress)
            metadatas = [c.metadata for c in chunks]
            doc_ids = self._memory.add_documents(texts, embeddings, metadatas)

            # Link doc to graph memory
            if self._graph:
                try:
                    cat = (metadata.get("category", "general") if metadata else "general") or "general"
                    self._graph.add_entity(file_path, "document", {"total_chunks": len(chunks), "category": cat})
                    self._graph.add_entity(cat, "category", {})
                    self._graph.add_relationship(file_path, cat, "belongs_to")
                except Exception:
                    pass

            progress.processed_chunks = len(chunks)
            progress.status = "completed"
            progress.phase = "done"
            if progress_callback:
                await progress_callback(progress)

        except Exception as e:
            progress.status = "error"
            progress.error = str(e)
            if progress_callback:
                await progress_callback(progress)

        return progress

    def get_ingestion_progress(self, task_id: str) -> Optional[IngestionProgress]:
        return self._ingestion_tasks.get(task_id)

    async def query(
        self, question: str, n_results: int = 5, provider: str = "groq", system_prompt: Optional[str] = None,
    ) -> RAGResponse:
        sources, context = await self._retriever.retrieve_with_context(question, n_results)

        sys_prompt = system_prompt or (
            "You are a helpful university assistant. Answer questions based on the provided context. "
            "If the context doesn't contain enough information, say so clearly. "
            "Always cite your sources by referencing the source numbers."
        )

        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ]

        response = await self._llm.generate(messages, provider=provider)

        return RAGResponse(
            answer=response.content,
            sources=sources,
            model=response.model,
            provider=response.provider,
            latency_ms=response.latency_ms,
            cost_usd=response.cost_usd,
        )

    async def search(self, query: str, n_results: int = 5) -> list[RetrievalResult]:
        return await self._retriever.retrieve(query, n_results)

    @property
    def retriever(self) -> SemanticRetriever:
        return self._retriever

    def update_chunker(self, chunk_size: int, chunk_overlap: int):
        self._chunker = TextChunker(chunk_size, chunk_overlap)
