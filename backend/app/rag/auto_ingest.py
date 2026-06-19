from __future__ import annotations
import asyncio
import os
from pathlib import Path
from typing import Optional

from app.rag.ingestion import FileParser, TextChunker
from app.rag.embeddings import EmbeddingGenerator
from app.memory.semantic import SemanticMemory
from app.observability.telemetry import log_event


DATA_DIR = Path(__file__).parent.parent.parent / "data"

INGEST_DIRS = [
    DATA_DIR / "JAVA",
    DATA_DIR / "Projet-Metier",
    DATA_DIR / "Time-Series",
    DATA_DIR / "UML",
    DATA_DIR,
]

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".md", ".txt", ".csv"}


async def auto_ingest_system_documents(
    semantic: SemanticMemory,
    embedder: EmbeddingGenerator,
    graph: Optional[Any] = None,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
):
    chunker = TextChunker(chunk_size, chunk_overlap)
    ingested = 0
    skipped = 0
    errors = []

    files_to_ingest = []
    for directory in INGEST_DIRS:
        if not directory.exists():
            continue
        for f in directory.iterdir():
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
                files_to_ingest.append(f)

    for file_path in files_to_ingest:
        source_name = file_path.name
        if semantic.is_source_ingested(source_name):
            skipped += 1
            continue

        try:
            doc = FileParser.parse(str(file_path))
            doc.metadata["source"] = source_name
            doc.metadata["system_document"] = "true"
            doc.metadata["category"] = file_path.parent.name if file_path.parent != DATA_DIR else "general"

            chunks = chunker.chunk(doc)
            if not chunks:
                continue

            for chunk in chunks:
                chunk.metadata["system_document"] = "true"
                chunk.metadata["source"] = source_name
                chunk.metadata["category"] = doc.metadata["category"]

            texts = [c.text for c in chunks]
            embeddings = await embedder.embed_batch(texts, use_cache=False)
            metadatas = [c.metadata for c in chunks]
            semantic.add_documents(texts, embeddings, metadatas)

            # Link doc to graph memory
            if graph:
                try:
                    cat = doc.metadata["category"]
                    graph.add_entity(source_name, "document", {"total_chunks": len(chunks), "category": cat})
                    graph.add_entity(cat, "category", {})
                    graph.add_relationship(source_name, cat, "belongs_to")
                except Exception:
                    pass

            ingested += 1

            log_event("system_ingest", {
                "file": source_name,
                "chunks": len(chunks),
                "category": doc.metadata["category"],
            })
        except Exception as e:
            errors.append({"file": source_name, "error": repr(e)})
            log_event("system_ingest_error", {"file": source_name, "error": repr(e)}, level="error")

    log_event("auto_ingest_complete", {
        "ingested": ingested,
        "skipped": skipped,
        "errors": len(errors),
        "total_files": len(files_to_ingest),
    })

    return {"ingested": ingested, "skipped": skipped, "errors": errors}
