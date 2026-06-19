from __future__ import annotations
import time
from fastapi import APIRouter, Depends

from app.api.schemas import SystemConfigResponse, RoutingToggleRequest, HealthResponse
from app.api.deps import get_kernel, get_router, get_memory

router = APIRouter(prefix="/api/system", tags=["system"])

_start_time = time.time()


@router.get("/health", response_model=HealthResponse)
async def health_check(kernel=Depends(get_kernel), memory=Depends(get_memory)):
    ollama_ok = await kernel.llm.ollama.health_check()
    groq_ok = await kernel.llm.groq.health_check()
    return HealthResponse(
        status="healthy" if ollama_ok else "degraded",
        ollama_healthy=ollama_ok,
        groq_healthy=groq_ok,
        memory_stats=memory.get_stats() if memory else {},
        uptime_seconds=round(time.time() - _start_time, 1),
    )


@router.get("/config", response_model=SystemConfigResponse)
async def get_config(kernel=Depends(get_kernel), model_router=Depends(get_router)):
    return SystemConfigResponse(
        ollama_model=kernel.llm.ollama.model,
        groq_model=kernel.llm.groq.model,
        local_only=model_router.local_only,
        rate_limit_rpm=60,
        chunk_size=512,
        chunk_overlap=50,
    )


@router.put("/routing")
async def toggle_routing(req: RoutingToggleRequest, model_router=Depends(get_router)):
    model_router.set_local_only(req.local_only)
    return {"local_only": model_router.local_only, "status": "updated"}


@router.get("/resources")
async def get_resources():
    import psutil
    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    return {
        "cpu_percent": cpu,
        "memory_percent": mem.percent,
        "memory_used_gb": round(mem.used / (1024**3), 2),
        "memory_total_gb": round(mem.total / (1024**3), 2),
    }


@router.put("/model")
async def switch_model(data: dict, kernel=Depends(get_kernel)):
    model = data.get("model", "")
    allowed = ["qwen2.5:3b", "qwen2.5:7b"]
    if model not in allowed:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Model must be one of: {allowed}")
    kernel.llm.ollama.model = model
    return {"status": "updated", "model": model}

