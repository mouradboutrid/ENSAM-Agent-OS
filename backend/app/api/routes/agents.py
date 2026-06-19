from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException

from app.api.schemas import DebateRequest, DebateResponse
from app.api.deps import get_agents, get_event_bus, get_debate_engine

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("")
async def list_agents(agents=Depends(get_agents)):
    return {
        "agents": [
            {"id": a.agent_id, "name": a.name, "description": a.description, "supported_tasks": a.supported_tasks}
            for a in agents.values()
        ]
    }


@router.get("/{agent_id}")
async def get_agent_info(agent_id: str, agents=Depends(get_agents)):
    agent = agents.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    return {"id": agent.agent_id, "name": agent.name, "description": agent.description, "supported_tasks": agent.supported_tasks}


@router.post("/debate", response_model=DebateResponse)
async def run_debate(req: DebateRequest, engine=Depends(get_debate_engine)):
    result = await engine.run_debate(
        topic=req.topic, agent_a_name=req.agent_a_name, agent_b_name=req.agent_b_name,
        rounds=req.rounds, force_local=req.force_local,
    )
    return DebateResponse(
        topic=result.topic,
        rounds=[{"agent_name": m.agent_name, "role": m.role, "content": m.content, "round_num": m.round_num} for m in result.rounds],
        synthesis=result.synthesis,
        total_rounds=result.total_rounds,
    )


@router.get("/events/log")
async def get_event_log(limit: int = 100, event_bus=Depends(get_event_bus)):
    events = event_bus.get_event_log(limit=limit)
    return {"events": [{"event_id": e.event_id, "type": e.type.value, "source": e.source, "timestamp": e.timestamp, "payload": e.payload} for e in events]}
