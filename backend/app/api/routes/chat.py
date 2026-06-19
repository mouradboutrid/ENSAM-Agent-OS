from __future__ import annotations
import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse

from app.api.schemas import ChatRequest, ChatResponse
from app.api.deps import get_kernel, get_agents, get_memory

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def send_message(req: ChatRequest, agents=Depends(get_agents), memory=Depends(get_memory)):
    agent = agents.get(req.agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {req.agent_id}")
    from app.agents.base import AgentContext
    ctx = AgentContext(
        session_id=req.session_id,
        user_id=req.user_id,
        force_local=req.force_local,
        force_cloud=req.force_cloud,
        language=req.language,
        web_search=req.web_search
    )
    try:
        result = await agent.process(req.message, ctx)
    except Exception as e:
        error_msg = str(e) or repr(e)
        if "ConnectError" in repr(e) or "ReadTimeout" in repr(e):
            error_msg = "Could not connect to the local Ollama server. Please make sure Ollama is running (`ollama serve`), or switch to **Cloud mode** in Settings."
        
        # Track failures in metrics
        try:
            from app.api.deps import get_metrics
            metrics = get_metrics()
            await metrics.record_error()
        except Exception:
            pass

        return ChatResponse(
            request_id=ctx.request_id,
            content=f"⚠️ **Error**: {error_msg}",
            agent_id=req.agent_id,
            agent_name="System",
            model="none",
            provider="error",
            sources=[],
            tool_calls=[],
            trace=[],
            usage={"error": error_msg},
        )
    # Record metrics
    try:
        from app.api.deps import get_metrics
        from app.observability.metrics import LatencyRecord
        metrics = get_metrics()
        await metrics.record_latency(LatencyRecord(
            request_id=ctx.request_id,
            agent_id=result.agent_id,
            total_ms=result.latency_ms,
            provider=result.provider,
        ))
    except Exception:
        pass

    return ChatResponse(
        request_id=ctx.request_id,
        content=result.content,
        agent_id=result.agent_id,
        agent_name=result.agent_name,
        model=result.model,
        provider=result.provider,
        sources=result.sources,
        tool_calls=result.tool_calls,
        trace=result.trace,
        usage={"input_tokens": 0, "output_tokens": 0, "cost_usd": result.cost_usd, "latency_ms": result.latency_ms},
    )


@router.get("/stream")
async def stream_chat(
    message: str, session_id: str = "default", agent_id: str = "tutor",
    user_id: str = "anonymous", force_local: bool = False, language: str = "en",
    agents=Depends(get_agents), kernel=Depends(get_kernel),
):
    agent = agents.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    async def event_generator():
        lang_instruction = "IMPORTANT: You must respond in French." if language == "fr" else "IMPORTANT: You must respond in English."
        sys_prompt = agent.get_system_prompt()
        if sys_prompt:
            sys_prompt += f"\n\n{lang_instruction}"
        else:
            sys_prompt = lang_instruction

        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": message},
        ]
        try:
            async for token in kernel.router.stream(messages, force_local=force_local):
                yield {"event": "token", "data": json.dumps({"token": token})}
            yield {"event": "done", "data": json.dumps({"status": "completed"})}
        except Exception as e:
            yield {"event": "error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(event_generator())


@router.get("/history/{session_id}")
async def get_history(session_id: str, memory=Depends(get_memory)):
    if not memory:
        return {"messages": []}
    messages = await memory.get_session_history(session_id)
    return {"session_id": session_id, "messages": messages}


@router.delete("/history/{session_id}")
async def clear_history(session_id: str, memory=Depends(get_memory)):
    if memory:
        await memory.ephemeral.clear_session(session_id)
    return {"status": "cleared", "session_id": session_id}
