from __future__ import annotations
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.core.llm import OllamaClient, GroqClient, LLMManager
from app.core.routing import ModelRouter
from app.core.events import EventBus
from app.core.kernel import AgentKernel
from app.memory.ephemeral import EphemeralMemory
from app.memory.semantic import SemanticMemory
from app.memory.graph import GraphMemory
from app.memory.manager import MemoryManager
from app.rag.embeddings import EmbeddingGenerator
from app.rag.pipeline import RAGPipeline
from app.mcp.registry import ToolRegistry
from app.mcp.client import MCPClient
from app.mcp.servers.schedule import get_schedule_tool
from app.mcp.servers.grades import get_grades_tool, get_gpa_calculator_tool
from app.mcp.servers.documents import get_documents_tool, get_web_search_tool
from app.agents.tutor import TutorAgent
from app.agents.admin import AdminAgent
from app.agents.orientation import OrientationAgent, SynthesisAgent
from app.agents.research import ResearchAgent
from app.agents.project import ProjectAgent
from app.agents.debate import DebateEngine
from app.agents.general import GeneralAgent
from app.agents.intent_classifier import IntentClassifier
from app.observability.telemetry import setup_telemetry
from app.observability.cost import CostTracker
from app.observability.audit import AuditLogger
from app.observability.metrics import MetricsCollector
from app.api.deps import set_app_state
from app.api.middleware import RequestIdMiddleware, RateLimitMiddleware, TimingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    setup_telemetry()

    ollama = OllamaClient(settings.ollama_base_url, settings.ollama_model, settings.request_timeout)
    groq = GroqClient(settings.groq_api_key, settings.groq_model, settings.groq_cost_per_1k_input, settings.groq_cost_per_1k_output, settings.max_retries)
    llm_manager = LLMManager(ollama, groq)
    router = ModelRouter(llm_manager)
    event_bus = EventBus()

    ephemeral = EphemeralMemory()
    semantic = SemanticMemory(settings.chroma_persist_dir)
    graph = GraphMemory(settings.graph_persist_dir)
    memory = MemoryManager(ephemeral, semantic, graph)

    embedding_gen = EmbeddingGenerator(ollama)
    rag = RAGPipeline(semantic, embedding_gen, llm_manager, graph, settings.chunk_size, settings.chunk_overlap)

    mcp_registry = ToolRegistry()
    await mcp_registry.register(get_schedule_tool())
    await mcp_registry.register(get_grades_tool())
    await mcp_registry.register(get_gpa_calculator_tool())
    await mcp_registry.register(get_documents_tool())
    await mcp_registry.register(get_web_search_tool())
    mcp_client = MCPClient(mcp_registry)

    cost_tracker = CostTracker()
    audit_logger = AuditLogger()
    metrics = MetricsCollector()

    kernel = AgentKernel(llm_manager, router, event_bus)
    kernel.set_memory_manager(memory)
    kernel.set_rag_pipeline(rag)
    kernel.set_mcp_registry(mcp_registry)
    kernel.set_cost_tracker(cost_tracker)
    kernel.set_audit_logger(audit_logger)

    agent_kwargs = dict(
        llm_manager=llm_manager, router=router, memory=memory, 
        mcp_client=mcp_client, rag=rag, event_bus=event_bus,
        cost_tracker=cost_tracker, audit_logger=audit_logger
    )
    specialist_agents = {
        "tutor": TutorAgent(**agent_kwargs),
        "admin": AdminAgent(**agent_kwargs),
        "orientation": OrientationAgent(**agent_kwargs),
        "synthesis": SynthesisAgent(**agent_kwargs),
        "research": ResearchAgent(**agent_kwargs),
        "project": ProjectAgent(**agent_kwargs),
    }
    intent_classifier = IntentClassifier()
    general_agent = GeneralAgent(agents_map=specialist_agents, intent_classifier=intent_classifier, **agent_kwargs)
    agents = {"general": general_agent, **specialist_agents}

    debate_engine = DebateEngine(llm_manager, router)

    for agent in agents.values():
        await event_bus.register_agent(agent.get_capability())

    set_app_state("kernel", kernel)
    set_app_state("router", router)
    set_app_state("agents", agents)
    set_app_state("memory", memory)
    set_app_state("rag", rag)
    set_app_state("mcp_registry", mcp_registry)
    set_app_state("mcp_client", mcp_client)
    set_app_state("event_bus", event_bus)
    set_app_state("cost_tracker", cost_tracker)
    set_app_state("audit_logger", audit_logger)
    set_app_state("metrics", metrics)
    set_app_state("debate_engine", debate_engine)

    from app.rag.auto_ingest import auto_ingest_system_documents
    asyncio.create_task(auto_ingest_system_documents(semantic, embedding_gen, graph, settings.chunk_size, settings.chunk_overlap))

    yield

    await llm_manager.close()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="ENSAM Agentic OS", version="0.1.0", description="Agentic Operating System for ENSAM University", lifespan=lifespan)

    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
    app.add_middleware(TimingMiddleware)
    app.add_middleware(RateLimitMiddleware, rpm=settings.rate_limit_rpm)
    app.add_middleware(RequestIdMiddleware)

    from app.api.routes import chat, agents, rag, mcp, observability, memory, system
    app.include_router(chat.router)
    app.include_router(agents.router)
    app.include_router(rag.router)
    app.include_router(mcp.router)
    app.include_router(observability.router)
    app.include_router(memory.router)
    app.include_router(system.router)

    @app.get("/")
    async def root():
        return {"name": "ENSAM Agentic OS", "version": "0.1.0", "status": "running"}

    return app


app = create_app()
