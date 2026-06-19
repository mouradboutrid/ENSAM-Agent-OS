from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException

from app.api.schemas import ToolTestRequest
from app.api.deps import get_mcp_registry, get_mcp_client

router = APIRouter(prefix="/api/mcp", tags=["mcp"])


@router.get("/tools")
async def list_tools(registry=Depends(get_mcp_registry)):
    return {"tools": registry.get_tools_summary()}


@router.get("/tools/{tool_id}")
async def get_tool(tool_id: str, registry=Depends(get_mcp_registry)):
    tool = registry.get_tool(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_id}")
    return {
        "tool_id": tool.tool_id, "name": tool.name, "description": tool.description,
        "security_level": tool.security_level.value, "status": tool.status.value,
        "tags": tool.tags, "registered_at": tool.registered_at,
        "parameters": [{"name": p.name, "type": p.type, "description": p.description, "required": p.required} for p in tool.parameters],
    }


@router.post("/tools/test")
async def test_tool(req: ToolTestRequest, registry=Depends(get_mcp_registry)):
    try:
        result = await registry.execute(req.tool_id, req.parameters, user_id=req.user_id, request_id="test")
        return {"tool_id": req.tool_id, "success": True, "result": result}
    except Exception as e:
        return {"tool_id": req.tool_id, "success": False, "error": str(e)}


@router.get("/tools/search/{query}")
async def search_tools(query: str, registry=Depends(get_mcp_registry)):
    tools = registry.discover(query)
    return {"query": query, "tools": [{"tool_id": t.tool_id, "name": t.name, "description": t.description} for t in tools]}


@router.get("/logs")
async def get_execution_logs(limit: int = 100, tool_id: str = None, registry=Depends(get_mcp_registry)):
    logs = registry.get_execution_log(limit=limit, tool_id=tool_id)
    return {
        "logs": [
            {"tool_id": l.tool_id, "input": l.input_data, "output": l.output_data,
             "error": l.error, "latency_ms": l.latency_ms, "timestamp": l.timestamp, "user_id": l.user_id}
            for l in logs
        ]
    }
