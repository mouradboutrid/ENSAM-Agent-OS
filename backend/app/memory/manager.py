from __future__ import annotations
from typing import Optional

from app.memory.ephemeral import EphemeralMemory
from app.memory.semantic import SemanticMemory
from app.memory.graph import GraphMemory
from app.memory.gdpr import GDPRManager


class MemoryManager:
    def __init__(self, ephemeral: EphemeralMemory, semantic: SemanticMemory, graph: GraphMemory):
        self.ephemeral = ephemeral
        self.semantic = semantic
        self.graph = graph
        self.gdpr = GDPRManager(ephemeral, semantic, graph)

    async def get_session_history(self, session_id: str) -> list[dict]:
        return await self.ephemeral.get_session_messages(session_id)

    async def save_message(self, session_id: str, user_id: str, content: str, role: str):
        await self.ephemeral.add_session_message(session_id, role, content)

    async def save_to_semantic(
        self, texts: list[str], embeddings: list[list[float]],
        metadatas: Optional[list[dict]] = None, ids: Optional[list[str]] = None,
    ) -> list[str]:
        return self.semantic.add_documents(texts, embeddings, metadatas, ids)

    def search_semantic(
        self, query_embedding: list[float], n_results: int = 5, where: Optional[dict] = None,
    ) -> dict:
        return self.semantic.search_documents(query_embedding, n_results, where)

    def add_graph_entity(self, entity_id: str, entity_type: str, properties: Optional[dict] = None):
        self.graph.add_entity(entity_id, entity_type, properties)

    def add_graph_relationship(self, source: str, target: str, relation_type: str, properties: Optional[dict] = None):
        self.graph.add_relationship(source, target, relation_type, properties)

    def get_graph_neighbors(self, entity_id: str, depth: int = 1) -> dict:
        return self.graph.get_neighbors(entity_id, depth)

    async def forget_user(self, user_id: str):
        return await self.gdpr.execute_right_to_be_forgotten(user_id)

    def get_stats(self) -> dict:
        return {
            "semantic": self.semantic.get_collection_stats(),
            "graph": self.graph.get_stats(),
        }
