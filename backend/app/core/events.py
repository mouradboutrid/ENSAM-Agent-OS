from __future__ import annotations
import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Coroutine, Optional


class EventType(str, Enum):
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    AGENT_REGISTER = "agent_register"
    AGENT_DEREGISTER = "agent_deregister"
    AGENT_DISCOVERY = "agent_discovery"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    MEMORY_WRITE = "memory_write"
    MEMORY_READ = "memory_read"
    GDPR_ERASE = "gdpr_erase"
    SYSTEM_ALERT = "system_alert"
    METRICS_UPDATE = "metrics_update"


@dataclass
class Event:
    type: EventType
    source: str
    payload: dict = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    correlation_id: Optional[str] = None
    target: Optional[str] = None


@dataclass
class AgentCapability:
    agent_id: str
    name: str
    description: str
    supported_tasks: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    status: str = "active"


EventHandler = Callable[[Event], Coroutine[Any, Any, None]]


class EventBus:
    def __init__(self):
        self._subscribers: dict[EventType, list[EventHandler]] = {}
        self._agent_registry: dict[str, AgentCapability] = {}
        self._event_log: list[Event] = []
        self._max_log_size = 10000
        self._lock = asyncio.Lock()

    def subscribe(self, event_type: EventType, handler: EventHandler):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: EventType, handler: EventHandler):
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                h for h in self._subscribers[event_type] if h != handler
            ]

    async def publish(self, event: Event):
        async with self._lock:
            self._event_log.append(event)
            if len(self._event_log) > self._max_log_size:
                self._event_log = self._event_log[-self._max_log_size:]
        handlers = self._subscribers.get(event.type, [])
        if handlers:
            await asyncio.gather(*(h(event) for h in handlers), return_exceptions=True)

    async def register_agent(self, capability: AgentCapability):
        self._agent_registry[capability.agent_id] = capability
        await self.publish(Event(
            type=EventType.AGENT_REGISTER, source="event_bus",
            payload={"agent_id": capability.agent_id, "name": capability.name, "tasks": capability.supported_tasks},
        ))

    async def deregister_agent(self, agent_id: str):
        self._agent_registry.pop(agent_id, None)
        await self.publish(Event(type=EventType.AGENT_DEREGISTER, source="event_bus", payload={"agent_id": agent_id}))

    def discover_agents(self, task_type: Optional[str] = None) -> list[AgentCapability]:
        if task_type is None:
            return list(self._agent_registry.values())
        return [c for c in self._agent_registry.values() if task_type in c.supported_tasks and c.status == "active"]

    def get_event_log(self, limit: int = 100, event_type: Optional[EventType] = None) -> list[Event]:
        log = self._event_log
        if event_type:
            log = [e for e in log if e.type == event_type]
        return log[-limit:]

    async def request_task(self, source: str, target: str, task_data: dict, correlation_id: Optional[str] = None) -> str:
        cid = correlation_id or str(uuid.uuid4())
        await self.publish(Event(type=EventType.TASK_REQUEST, source=source, target=target, payload=task_data, correlation_id=cid))
        return cid
