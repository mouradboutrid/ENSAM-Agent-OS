from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str
    session_id: str = Field(default="default")
    user_id: str = Field(default="anonymous")
    agent_id: str = Field(default="tutor")
    force_local: bool = Field(default=False)
    force_cloud: bool = Field(default=False)
    language: str = Field(default="en")
    web_search: bool = Field(default=False)


class ChatResponse(BaseModel):
    request_id: str
    content: str
    agent_id: str
    agent_name: str
    model: str
    provider: str
    sources: list[dict] = []
    tool_calls: list[dict] = []
    trace: list[dict] = []
    usage: dict = {}


class DebateRequest(BaseModel):
    topic: str
    agent_a_name: str = Field(default="Proponent")
    agent_b_name: str = Field(default="Opponent")
    rounds: int = Field(default=3, ge=1, le=10)
    force_local: bool = Field(default=False)


class DebateResponse(BaseModel):
    topic: str
    rounds: list[dict]
    synthesis: str
    total_rounds: int


class IngestRequest(BaseModel):
    chunk_size: int = Field(default=512, ge=100, le=4096)
    chunk_overlap: int = Field(default=50, ge=0, le=500)
    metadata: dict = Field(default_factory=dict)


class IngestResponse(BaseModel):
    task_id: str
    filename: str
    status: str
    total_chunks: int
    processed_chunks: int


class SearchRequest(BaseModel):
    query: str
    n_results: int = Field(default=5, ge=1, le=50)
    provider: str = Field(default="groq")


class SearchResponse(BaseModel):
    results: list[dict]
    query: str


class RAGQueryRequest(BaseModel):
    question: str
    n_results: int = Field(default=5, ge=1, le=20)
    provider: str = Field(default="groq")


class RAGQueryResponse(BaseModel):
    answer: str
    sources: list[dict]
    model: str
    provider: str
    latency_ms: float
    cost_usd: float


class ToolTestRequest(BaseModel):
    tool_id: str
    parameters: dict = Field(default_factory=dict)
    user_id: str = Field(default="test")


class GDPRForgetRequest(BaseModel):
    user_id: str
    confirm: bool = Field(default=False)


class GDPRForgetResponse(BaseModel):
    user_id: str
    status: str
    ephemeral_deleted: int
    semantic_deleted: dict
    graph_deleted: int
    errors: list[str]


class SystemConfigResponse(BaseModel):
    ollama_model: str
    groq_model: str
    local_only: bool
    rate_limit_rpm: int
    chunk_size: int
    chunk_overlap: int


class RoutingToggleRequest(BaseModel):
    local_only: bool


class HealthResponse(BaseModel):
    status: str
    ollama_healthy: bool
    groq_healthy: bool
    memory_stats: dict
    uptime_seconds: float
