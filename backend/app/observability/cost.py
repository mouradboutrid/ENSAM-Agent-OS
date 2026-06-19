from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.core.llm import LLMResponse


@dataclass
class CostRecord:
    request_id: str
    user_id: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CostTracker:
    def __init__(self):
        self._records: list[CostRecord] = []
        self._user_totals: dict[str, float] = {}
        self._provider_totals: dict[str, float] = {}
        self._lock = asyncio.Lock()
        self._max_records = 50000

    async def record(self, response: LLMResponse, user_id: str, request_id: str):
        async with self._lock:
            rec = CostRecord(
                request_id=request_id, user_id=user_id, provider=response.provider,
                model=response.model, input_tokens=response.input_tokens,
                output_tokens=response.output_tokens, cost_usd=response.cost_usd,
            )
            self._records.append(rec)
            if len(self._records) > self._max_records:
                self._records = self._records[-self._max_records:]
            self._user_totals[user_id] = self._user_totals.get(user_id, 0) + response.cost_usd
            self._provider_totals[response.provider] = self._provider_totals.get(response.provider, 0) + response.cost_usd

    def get_total_cost(self) -> float:
        return sum(r.cost_usd for r in self._records)

    def get_user_cost(self, user_id: str) -> float:
        return self._user_totals.get(user_id, 0)

    def get_provider_breakdown(self) -> dict:
        return self._provider_totals.copy()

    def get_token_usage(self) -> dict:
        total_input = sum(r.input_tokens for r in self._records)
        total_output = sum(r.output_tokens for r in self._records)
        return {
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "total_requests": len(self._records),
        }

    def get_recent_records(self, limit: int = 100, user_id: Optional[str] = None) -> list[dict]:
        records = self._records
        if user_id:
            records = [r for r in records if r.user_id == user_id]
        return [
            {"request_id": r.request_id, "user_id": r.user_id, "provider": r.provider, "model": r.model,
             "input_tokens": r.input_tokens, "output_tokens": r.output_tokens, "cost_usd": r.cost_usd, "timestamp": r.timestamp}
            for r in records[-limit:]
        ]

    def get_savings_report(self) -> dict:
        groq_cost = self._provider_totals.get("groq", 0)
        local_requests = sum(1 for r in self._records if r.provider == "ollama")
        groq_requests = sum(1 for r in self._records if r.provider == "groq")
        local_tokens = sum(r.input_tokens + r.output_tokens for r in self._records if r.provider == "ollama")
        estimated_savings = local_tokens / 1000 * 0.00059
        return {
            "groq_cost_usd": groq_cost,
            "local_requests": local_requests,
            "groq_requests": groq_requests,
            "estimated_savings_usd": estimated_savings,
            "total_requests": len(self._records),
        }
