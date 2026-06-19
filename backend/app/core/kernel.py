from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.events import EventBus, Event, EventType, AgentCapability
from app.core.routing import ModelRouter, RoutingDecision
from app.core.llm import LLMManager, LLMResponse


@dataclass
class RequestContext:
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    trace: list[dict] = field(default_factory=list)
    routing_decision: Optional[RoutingDecision] = None
    force_local: bool = False

    def add_trace(self, step: str, data: dict):
        self.trace.append({"step": step, "timestamp": datetime.now(timezone.utc).isoformat(), **data})


class AgentKernel:
    def __init__(self, llm_manager: LLMManager, router: ModelRouter, event_bus: EventBus):
        self.llm = llm_manager
        self.router = router
        self.event_bus = event_bus
        self._agents: dict[str, Any] = {}
        self._memory_manager = None
        self._rag_pipeline = None
        self._mcp_registry = None
        self._cost_tracker = None
        self._audit_logger = None
        self._active_requests: dict[str, RequestContext] = {}

    def set_memory_manager(self, manager):
        self._memory_manager = manager

    def set_rag_pipeline(self, pipeline):
        self._rag_pipeline = pipeline

    def set_mcp_registry(self, registry):
        self._mcp_registry = registry

    def set_cost_tracker(self, tracker):
        self._cost_tracker = tracker

    def set_audit_logger(self, logger):
        self._audit_logger = logger

    async def register_agent(self, agent_id: str, agent: Any, capability: AgentCapability):
        self._agents[agent_id] = agent
        await self.event_bus.register_agent(capability)

    async def process_request(
        self, messages: list[dict], session_id: str, user_id: str = "anonymous",
        agent_id: Optional[str] = None, force_local: bool = False,
    ) -> dict:
        ctx = RequestContext(session_id=session_id, user_id=user_id, agent_id=agent_id, force_local=force_local)
        self._active_requests[ctx.request_id] = ctx

        try:
            ctx.add_trace("request_received", {"message_count": len(messages), "agent_id": agent_id})

            if self._memory_manager:
                history = await self._memory_manager.get_session_history(session_id)
                if history:
                    ctx.add_trace("memory_loaded", {"history_length": len(history)})

            response, decision = await self.router.generate(messages, force_local=force_local)
            ctx.routing_decision = decision
            ctx.add_trace("routing_decided", {
                "target": decision.target.value, "complexity": decision.complexity.value,
                "reason": decision.reason, "privacy_flag": decision.privacy_flag,
            })
            ctx.add_trace("llm_response", {
                "provider": response.provider, "model": response.model,
                "input_tokens": response.input_tokens, "output_tokens": response.output_tokens,
                "latency_ms": response.latency_ms, "cost_usd": response.cost_usd,
            })

            if self._memory_manager:
                await self._memory_manager.save_message(session_id, user_id, messages[-1].get("content", ""), "user")
                await self._memory_manager.save_message(session_id, user_id, response.content, "assistant")

            if self._cost_tracker:
                await self._cost_tracker.record(response, user_id, ctx.request_id)

            if self._audit_logger:
                await self._audit_logger.log(ctx)

            await self.event_bus.publish(Event(
                type=EventType.METRICS_UPDATE, source="kernel",
                payload={"request_id": ctx.request_id, "latency_ms": response.latency_ms, "cost_usd": response.cost_usd, "provider": response.provider},
            ))

            return {
                "request_id": ctx.request_id,
                "content": response.content,
                "model": response.model,
                "provider": response.provider,
                "routing": {"target": decision.target.value, "reason": decision.reason, "complexity": decision.complexity.value, "privacy_flag": decision.privacy_flag},
                "usage": {"input_tokens": response.input_tokens, "output_tokens": response.output_tokens, "cost_usd": response.cost_usd, "latency_ms": response.latency_ms},
                "trace": ctx.trace,
            }
        finally:
            self._active_requests.pop(ctx.request_id, None)

    def get_registered_agents(self) -> list[AgentCapability]:
        return self.event_bus.discover_agents()

    def get_active_requests(self) -> dict[str, RequestContext]:
        return self._active_requests.copy()
