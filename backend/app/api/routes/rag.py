from __future__ import annotations
import json
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sse_starlette.sse import EventSourceResponse
from typing import Optional

from app.api.schemas import IngestResponse, SearchRequest, RAGQueryRequest, RAGQueryResponse
from app.api.deps import get_rag_pipeline, get_memory

router = APIRouter(prefix="/api/rag", tags=["rag"])


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile = File(...),
    chunk_size: int = Form(default=512),
    chunk_overlap: int = Form(default=50),
    metadata: str = Form(default="{}"),
    rag=Depends(get_rag_pipeline),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    content = await file.read()
    try:
        meta = json.loads(metadata)
    except json.JSONDecodeError:
        meta = {}
    meta["original_filename"] = file.filename
    rag.update_chunker(chunk_size, chunk_overlap)
    progress = await rag.ingest_file(file.filename, content_bytes=content, metadata=meta)
    return IngestResponse(
        task_id=progress.task_id, filename=progress.filename,
        status=progress.status, total_chunks=progress.total_chunks, processed_chunks=progress.processed_chunks,
    )


@router.post("/search")
async def semantic_search(req: SearchRequest, rag=Depends(get_rag_pipeline)):
    results = await rag.search(req.query, n_results=req.n_results)
    return {
        "query": req.query,
        "results": [{"text": r.text, "score": r.score, "metadata": r.metadata, "doc_id": r.doc_id} for r in results],
    }


@router.post("/query", response_model=RAGQueryResponse)
async def rag_query(req: RAGQueryRequest, rag=Depends(get_rag_pipeline)):
    result = await rag.query(req.question, n_results=req.n_results, provider=req.provider)
    return RAGQueryResponse(
        answer=result.answer,
        sources=[{"text": s.text[:300], "score": s.score, "doc_id": s.doc_id, "metadata": s.metadata} for s in result.sources],
        model=result.model, provider=result.provider, latency_ms=result.latency_ms, cost_usd=result.cost_usd,
    )


@router.get("/documents")
async def list_documents(limit: int = 100, offset: int = 0, memory=Depends(get_memory)):
    data = memory.semantic.list_documents(limit=limit, offset=offset)
    docs = []
    if data and data.get("ids"):
        for i, doc_id in enumerate(data["ids"]):
            docs.append({
                "id": doc_id,
                "text_preview": (data["documents"][i][:200] + "...") if data.get("documents") and data["documents"][i] else "",
                "metadata": data["metadatas"][i] if data.get("metadatas") else {},
            })
    return {"documents": docs, "total": len(docs)}


@router.get("/stats")
async def rag_stats(memory=Depends(get_memory)):
    return memory.semantic.get_collection_stats()


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, memory=Depends(get_memory)):
    doc = memory.semantic.get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.get("metadata", {}).get("system_document") == "true":
        raise HTTPException(status_code=403, detail="Cannot delete system documents")
    success = memory.semantic.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete document")
    return {"status": "deleted", "doc_id": doc_id}
