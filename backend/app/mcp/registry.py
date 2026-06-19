from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Coroutine, Optional


class ToolStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class SecurityLevel(str, Enum):
    PUBLIC = "public"
    STUDENT = "student"
    FACULTY = "faculty"
    ADMIN = "admin"


@dataclass
class ToolParameter:
    name: str
    type: str
    description: str = ""
    required: bool = True
    default: Any = None


@dataclass
class ToolDefinition:
    tool_id: str
    name: str
    description: str
    parameters: list[ToolParameter] = field(default_factory=list)
    security_level: SecurityLevel = SecurityLevel.PUBLIC
    server_name: str = ""
    status: ToolStatus = ToolStatus.ACTIVE
    tags: list[str] = field(default_factory=list)
    registered_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    handler: Optional[Callable] = field(default=None, repr=False)


@dataclass
class ToolExecutionLog:
    tool_id: str
    input_data: dict
    output_data: Any = None
    error: Optional[str] = None
    latency_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    user_id: str = ""
    request_id: str = ""


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}
        self._execution_log: list[ToolExecutionLog] = []
        self._max_log_size = 5000
        self._lock = asyncio.Lock()

    async def register(self, tool: ToolDefinition):
        async with self._lock:
            self._tools[tool.tool_id] = tool

    async def deregister(self, tool_id: str):
        async with self._lock:
            self._tools.pop(tool_id, None)

    def get_tool(self, tool_id: str) -> Optional[ToolDefinition]:
        return self._tools.get(tool_id)

    def list_tools(self, security_level: Optional[SecurityLevel] = None, tags: Optional[list[str]] = None) -> list[ToolDefinition]:
        tools = list(self._tools.values())
        if security_level:
            level_order = [SecurityLevel.PUBLIC, SecurityLevel.STUDENT, SecurityLevel.FACULTY, SecurityLevel.ADMIN]
            max_idx = level_order.index(security_level)
            tools = [t for t in tools if level_order.index(t.security_level) <= max_idx]
        if tags:
            tools = [t for t in tools if any(tag in t.tags for tag in tags)]
        return tools

    def discover(self, query: str) -> list[ToolDefinition]:
        query_lower = query.lower()
        return [
            t for t in self._tools.values()
            if query_lower in t.name.lower() or query_lower in t.description.lower() or any(query_lower in tag for tag in t.tags)
        ]

    async def execute(self, tool_id: str, params: dict, user_id: str = "", request_id: str = "") -> Any:
        tool = self.get_tool(tool_id)
        if not tool:
            raise ValueError(f"Tool not found: {tool_id}")
        if tool.status != ToolStatus.ACTIVE:
            raise RuntimeError(f"Tool is not active: {tool_id}")
        if not tool.handler:
            raise RuntimeError(f"Tool has no handler: {tool_id}")

        import time
        start = time.perf_counter()
        log = ToolExecutionLog(tool_id=tool_id, input_data=params, user_id=user_id, request_id=request_id)

        try:
            if asyncio.iscoroutinefunction(tool.handler):
                result = await tool.handler(**params)
            else:
                result = tool.handler(**params)
            log.output_data = result
            log.latency_ms = (time.perf_counter() - start) * 1000
        except Exception as e:
            log.error = str(e)
            log.latency_ms = (time.perf_counter() - start) * 1000
            self._execution_log.append(log)
            raise

        self._execution_log.append(log)
        if len(self._execution_log) > self._max_log_size:
            self._execution_log = self._execution_log[-self._max_log_size:]
        return result

    def get_execution_log(self, limit: int = 100, tool_id: Optional[str] = None) -> list[ToolExecutionLog]:
        log = self._execution_log
        if tool_id:
            log = [e for e in log if e.tool_id == tool_id]
        return log[-limit:]

    def get_tools_summary(self) -> list[dict]:
        return [
            {"tool_id": t.tool_id, "name": t.name, "description": t.description, "status": t.status.value, "security_level": t.security_level.value, "tags": t.tags}
            for t in self._tools.values()
        ]
