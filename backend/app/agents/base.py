from __future__ import annotations
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.events import EventBus, Event, EventType, AgentCapability
from app.core.llm import LLMManager, LLMResponse
from app.core.routing import ModelRouter
from app.memory.manager import MemoryManager
from app.mcp.client import MCPClient
from app.rag.pipeline import RAGPipeline


@dataclass
class AgentContext:
    session_id: str
    user_id: str = "anonymous"
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    force_local: bool = False
    force_cloud: bool = False
    language: str = "en"
    web_search: bool = False
    metadata: dict = field(default_factory=dict)


@dataclass
class AgentResponse:
    content: str
    agent_id: str
    agent_name: str
    sources: list[dict] = field(default_factory=list)
    tool_calls: list[dict] = field(default_factory=list)
    trace: list[dict] = field(default_factory=list)
    model: str = ""
    provider: str = ""
    latency_ms: float = 0.0
    cost_usd: float = 0.0


class BaseAgent(ABC):
    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        llm_manager: LLMManager,
        router: ModelRouter,
        memory: Optional[MemoryManager] = None,
        mcp_client: Optional[MCPClient] = None,
        rag: Optional[RAGPipeline] = None,
        event_bus: Optional[EventBus] = None,
        supported_tasks: Optional[list[str]] = None,
        cost_tracker: Optional[Any] = None,
        audit_logger: Optional[Any] = None,
    ):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.llm = llm_manager
        self.router = router
        self.memory = memory
        self.mcp = mcp_client
        self.rag = rag
        self.event_bus = event_bus
        self.supported_tasks = supported_tasks or []
        self.cost_tracker = cost_tracker
        self.audit_logger = audit_logger
        self._trace: list[dict] = []

    def get_capability(self) -> AgentCapability:
        return AgentCapability(
            agent_id=self.agent_id,
            name=self.name,
            description=self.description,
            supported_tasks=self.supported_tasks,
        )

    def _add_trace(self, step: str, data: dict):
        self._trace.append({"step": step, "timestamp": datetime.now(timezone.utc).isoformat(), "agent": self.agent_id, **data})

    @abstractmethod
    def get_system_prompt(self) -> str: ...

    async def process(self, query: str, context: AgentContext) -> AgentResponse:
        self._trace = []
        self._add_trace("agent_start", {"query": query[:200]})

        lang_instruction = "IMPORTANT: You must respond in French." if context.language == "fr" else "IMPORTANT: You must respond in English."
        sys_prompt = self.get_system_prompt()
        if sys_prompt:
            sys_prompt += f"\n\n{lang_instruction}"
        else:
            sys_prompt = lang_instruction
            
        messages = [{"role": "system", "content": sys_prompt}]

        if self.memory:
            history = await self.memory.get_session_history(context.session_id)
            for msg in history[-10:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
            self._add_trace("history_loaded", {"count": len(history)})

        if getattr(context, "web_search", False):
            try:
                from app.core.web_search import search_web_ddg
                search_results = search_web_ddg(query)
                messages.append({"role": "system", "content": search_results})
                self._add_trace("web_search", {"query": query, "success": True})
            except Exception as e:
                self._add_trace("web_search", {"query": query, "success": False, "error": str(e)})

        rag_sources = []
        if self.rag and self._should_use_rag(query):
            rag_result = await self.rag.query(query, n_results=3)
            if rag_result.sources:
                rag_context = "\n\n".join([f"[Source {i+1}]: {s.text}" for i, s in enumerate(rag_result.sources)])
                messages.append({"role": "system", "content": f"Relevant context from knowledge base:\n{rag_context}"})
                rag_sources = [{"text": s.text[:200], "score": s.score, "doc_id": s.doc_id} for s in rag_result.sources]
                self._add_trace("rag_retrieval", {"sources_found": len(rag_result.sources)})

        tool_results = []
        if self.mcp:
            tools = await self._select_tools(query)
            for tool_id, params in tools:
                try:
                    result = await self.mcp.call_simple(tool_id, params, user_id=context.user_id)
                    tool_results.append({"tool_id": tool_id, "result": result})
                    messages.append({"role": "system", "content": f"Tool [{tool_id}] result: {result}"})
                    self._add_trace("tool_call", {"tool_id": tool_id, "success": True})
                except Exception as e:
                    self._add_trace("tool_call", {"tool_id": tool_id, "success": False, "error": str(e)})

        messages.append({"role": "user", "content": query})

        response, decision = await self.router.generate(messages, force_local=context.force_local, force_cloud=context.force_cloud)
        self._add_trace("llm_response", {"provider": response.provider, "model": response.model, "tokens": response.input_tokens + response.output_tokens})

        # Record LLM cost statistics
        if self.cost_tracker and response:
            await self.cost_tracker.record(response, context.user_id, context.request_id)

        # Log request and trace to Audit Log
        if self.audit_logger:
            try:
                from types import SimpleNamespace
                aud_ctx = SimpleNamespace(
                    request_id=context.request_id,
                    session_id=context.session_id,
                    user_id=context.user_id,
                    agent_id=self.agent_id,
                    trace=self._trace,
                    routing_decision=decision
                )
                await self.audit_logger.log(aud_ctx)
            except Exception:
                pass

        if self.memory:
            await self.memory.save_message(context.session_id, context.user_id, query, "user")
            await self.memory.save_message(context.session_id, context.user_id, response.content, "assistant")

        if self.event_bus:
            await self.event_bus.publish(Event(
                type=EventType.TASK_RESPONSE, source=self.agent_id,
                payload={"request_id": context.request_id, "status": "completed"},
            ))

        return AgentResponse(
            content=response.content,
            agent_id=self.agent_id,
            agent_name=self.name,
            sources=rag_sources,
            tool_calls=tool_results,
            trace=self._trace.copy(),
            model=response.model,
            provider=response.provider,
            latency_ms=response.latency_ms,
            cost_usd=response.cost_usd,
        )

    def _should_use_rag(self, query: str) -> bool:
        return True

    async def _select_tools(self, query: str) -> list[tuple[str, dict]]:
        return []
