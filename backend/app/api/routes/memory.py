from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException

from app.api.schemas import GDPRForgetRequest, GDPRForgetResponse
from app.api.deps import get_memory

router = APIRouter(prefix="/api/memory", tags=["memory"])


@router.get("/stats")
async def memory_stats(memory=Depends(get_memory)):
    return memory.get_stats()


@router.get("/graph")
async def get_graph(memory=Depends(get_memory)):
    return memory.graph.get_full_graph()


@router.get("/graph/{entity_id}")
async def get_graph_entity(entity_id: str, depth: int = 1, memory=Depends(get_memory)):
    entity = memory.graph.get_entity(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity not found: {entity_id}")
    neighbors = memory.graph.get_neighbors(entity_id, depth)
    return {"entity": entity, "neighbors": neighbors}


@router.get("/sessions")
async def list_sessions(memory=Depends(get_memory)):
    keys = await memory.ephemeral.get_all_keys()
    sessions = list(set(k.split(":")[1] for k in keys if k.startswith("session:")))
    return {"sessions": sessions}


@router.post("/gdpr/forget", response_model=GDPRForgetResponse)
async def forget_user(req: GDPRForgetRequest, memory=Depends(get_memory)):
    if not req.confirm:
        raise HTTPException(status_code=400, detail="Must confirm erasure by setting confirm=true")
    result = await memory.forget_user(req.user_id)
    return GDPRForgetResponse(
        user_id=result.user_id, status=result.status,
        ephemeral_deleted=result.ephemeral_deleted, semantic_deleted=result.semantic_deleted,
        graph_deleted=result.graph_deleted, errors=result.errors,
    )


@router.get("/gdpr/verify/{user_id}")
async def verify_erasure(user_id: str, memory=Depends(get_memory)):
    return await memory.gdpr.verify_erasure(user_id)


@router.get("/gdpr/log")
async def get_erasure_log(memory=Depends(get_memory)):
    return {"erasure_log": memory.gdpr.get_erasure_log()}
