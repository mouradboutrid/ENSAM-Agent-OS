from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ErasureRecord:
    user_id: str
    timestamp: str
    ephemeral_deleted: int = 0
    semantic_deleted: dict = field(default_factory=dict)
    graph_deleted: int = 0
    status: str = "pending"
    errors: list[str] = field(default_factory=list)


class GDPRManager:
    def __init__(self, ephemeral, semantic, graph):
        self._ephemeral = ephemeral
        self._semantic = semantic
        self._graph = graph
        self._erasure_log: list[ErasureRecord] = []

    async def execute_right_to_be_forgotten(self, user_id: str) -> ErasureRecord:
        record = ErasureRecord(
            user_id=user_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        try:
            count = await self._ephemeral.delete_user_data(user_id)
            record.ephemeral_deleted = count
        except Exception as e:
            record.errors.append(f"ephemeral: {str(e)}")

        try:
            result = self._semantic.delete_user_data(user_id)
            record.semantic_deleted = result
        except Exception as e:
            record.errors.append(f"semantic: {str(e)}")

        try:
            count = self._graph.delete_user_data(user_id)
            record.graph_deleted = count
        except Exception as e:
            record.errors.append(f"graph: {str(e)}")

        record.status = "completed" if not record.errors else "partial"
        self._erasure_log.append(record)
        return record

    async def verify_erasure(self, user_id: str) -> dict:
        ephemeral_keys = await self._ephemeral.get_user_keys(user_id)
        graph_entity = self._graph.get_entity(user_id)
        return {
            "user_id": user_id,
            "ephemeral_remaining": len(ephemeral_keys),
            "graph_remaining": 1 if graph_entity else 0,
            "fully_erased": len(ephemeral_keys) == 0 and graph_entity is None,
        }

    def get_erasure_log(self) -> list[dict]:
        return [
            {
                "user_id": r.user_id,
                "timestamp": r.timestamp,
                "ephemeral_deleted": r.ephemeral_deleted,
                "semantic_deleted": r.semantic_deleted,
                "graph_deleted": r.graph_deleted,
                "status": r.status,
                "errors": r.errors,
            }
            for r in self._erasure_log
        ]
