from __future__ import annotations
from fastapi import APIRouter, Depends

from app.api.deps import get_cost_tracker, get_metrics, get_audit_logger, get_event_bus

router = APIRouter(prefix="/api/observability", tags=["observability"])


@router.get("/metrics")
async def get_system_metrics(metrics=Depends(get_metrics)):
    return metrics.get_summary()


@router.get("/metrics/latency")
async def get_latency_metrics(metrics=Depends(get_metrics)):
    return {"latency": metrics.get_latency_stats(), "by_provider": metrics.get_provider_latency()}


@router.get("/metrics/latency/recent")
async def get_recent_latencies(limit: int = 50, metrics=Depends(get_metrics)):
    return {"records": metrics.get_recent_latencies(limit)}


@router.get("/metrics/resources")
async def get_resource_metrics(metrics=Depends(get_metrics)):
    return metrics.get_system_resources()


@router.get("/costs")
async def get_cost_metrics(cost=Depends(get_cost_tracker)):
    return {
        "total_cost_usd": cost.get_total_cost(),
        "by_provider": cost.get_provider_breakdown(),
        "token_usage": cost.get_token_usage(),
        "savings": cost.get_savings_report(),
    }


@router.get("/costs/records")
async def get_cost_records(limit: int = 100, user_id: str = None, cost=Depends(get_cost_tracker)):
    return {"records": cost.get_recent_records(limit, user_id)}


@router.get("/audit")
async def get_audit_entries(limit: int = 100, user_id: str = None, audit=Depends(get_audit_logger)):
    return {"entries": audit.get_entries(limit, user_id), "stats": audit.get_stats()}


@router.post("/audit/export")
async def export_audit_log(audit=Depends(get_audit_logger)):
    filepath = await audit.export_json()
    return {"status": "exported", "filepath": filepath}


@router.get("/traces")
async def get_traces(limit: int = 100, event_bus=Depends(get_event_bus)):
    events = event_bus.get_event_log(limit=limit)
    return {
        "traces": [
            {"event_id": e.event_id, "type": e.type.value, "source": e.source,
             "timestamp": e.timestamp, "payload": e.payload, "correlation_id": e.correlation_id}
            for e in events
        ]
    }
