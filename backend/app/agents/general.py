from __future__ import annotations
import logging
from datetime import datetime
from typing import Optional

from app.agents.base import BaseAgent, AgentContext, AgentResponse
from app.agents.intent_classifier import IntentClassifier, get_intent_classifier
from app.core.llm import LLMManager
from app.core.routing import ModelRouter
from app.memory.manager import MemoryManager
from app.mcp.client import MCPClient
from app.rag.pipeline import RAGPipeline
from app.core.events import EventBus

logger = logging.getLogger(__name__)

# Minimum confidence threshold — below this we try keyword fallback
CONFIDENCE_THRESHOLD = 0.35


class GeneralAgent(BaseAgent):
    def __init__(self, agents_map: dict, intent_classifier: Optional[IntentClassifier] = None, **kwargs):
        super().__init__(
            agent_id="general",
            name="General Assistant",
            description="Smart router that automatically detects your intent and delegates to the best specialist agent",
            supported_tasks=["general", "auto_route", "any"],
            **kwargs,
        )
        self._agents_map = agents_map
        self._classifier = intent_classifier or get_intent_classifier()
        # Dynamically register agent capabilities for embedding routing
        self._classifier.register_agents(self._agents_map)

    def get_system_prompt(self) -> str:
        return ""

    async def process(self, query: str, context: AgentContext) -> AgentResponse:
        self._trace = []
        self._add_trace("general_start", {"query": query[:200]})

        # Classify intent using the fast local classifier
        result = self._classifier.classify(query)
        intent = result.intent
        confidence = result.confidence

        self._add_trace("intent_classified", {
            "intent": intent,
            "confidence": confidence,
            "method": result.method,
            "scores": result.scores,
        })

        # If confidence is too low, try keyword fallback
        if confidence < CONFIDENCE_THRESHOLD and result.method != "keyword-fallback":
            fallback_intent = self._keyword_fallback(query)
            self._add_trace("low_confidence_fallback", {
                "original_intent": intent,
                "original_confidence": confidence,
                "fallback_intent": fallback_intent,
            })
            intent = fallback_intent

        target_agent = self._agents_map.get(intent)
        if not target_agent:
            target_agent = self._agents_map.get("tutor")
            intent = "tutor"
            self._add_trace("fallback_agent", {"reason": "unknown_intent", "fallback": intent})

        logger.info(f"Routing to '{intent}' agent (confidence={confidence:.2f}, method={result.method})")

        # Log decision path to graph memory
        if self.memory and self.memory.graph:
            try:
                query_node_id = f"q_{context.request_id[:8]}"
                self.memory.graph.add_entity(query_node_id, "query", {"text": query[:50], "timestamp": datetime.now().isoformat()})
                self.memory.graph.add_entity(context.session_id, "session", {"user_id": context.user_id})
                self.memory.graph.add_entity(intent, "agent", {"name": target_agent.name})
                self.memory.graph.add_relationship(context.session_id, query_node_id, "contains_query")
                self.memory.graph.add_relationship(query_node_id, intent, "routed_to")
            except Exception as e:
                logger.warning(f"Failed to log query routing to graph memory: {e}")

        agent_result = await target_agent.process(query, context)
        agent_result.trace = self._trace + agent_result.trace
        agent_result.agent_name = f"{agent_result.agent_name} (via General)"

        return agent_result

    def _keyword_fallback(self, query: str) -> str:
        """Simple keyword fallback for very ambiguous queries."""
        query_lower = query.lower()
        if any(kw in query_lower for kw in ["schedule", "emploi", "note", "grade", "horaire", "salle", "inscription", "examen"]):
            return "admin"
        if any(kw in query_lower for kw in ["career", "carrière", "orientation", "métier", "job", "stage", "emploi"]):
            return "orientation"
        if any(kw in query_lower for kw in ["summarize", "résumé", "report", "synthèse", "compare", "guide"]):
            return "synthesis"
        return "tutor"
