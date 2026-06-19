from __future__ import annotations
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from app.core.llm import LLMManager, LLMResponse


class RouteTarget(str, Enum):
    LOCAL = "ollama"
    CLOUD = "groq"


class TaskComplexity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class RoutingDecision:
    target: RouteTarget
    complexity: TaskComplexity
    reason: str
    privacy_flag: bool = False
    estimated_tokens: int = 0


PII_PATTERNS = [
    r"\b\d{8,10}\b",
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
    r"\b(?:CNE|CIN|passport)\s*[:=]?\s*\w+",
]

HIGH_COMPLEXITY_INDICATORS = [
    "compare", "analyze", "synthesize", "debate", "evaluate",
    "explain in detail", "write an essay", "generate a report",
    "multi-step", "research", "comprehensive", "critically",
    "pros and cons", "trade-offs", "architecture",
]

LOW_COMPLEXITY_INDICATORS = [
    "what is", "define", "list", "when is", "where is",
    "who is", "translate", "summarize briefly", "yes or no",
    "schedule", "grade", "simple", "quick",
]


class QueryAnalyzer:
    def __init__(self):
        self._pii_patterns = [re.compile(p, re.IGNORECASE) for p in PII_PATTERNS]

    def detect_pii(self, text: str) -> bool:
        return any(p.search(text) for p in self._pii_patterns)

    def estimate_complexity(self, text: str) -> TaskComplexity:
        text_lower = text.lower()
        high_score = sum(1 for ind in HIGH_COMPLEXITY_INDICATORS if ind in text_lower)
        low_score = sum(1 for ind in LOW_COMPLEXITY_INDICATORS if ind in text_lower)
        word_count = len(text.split())

        if high_score >= 2 or word_count > 200:
            return TaskComplexity.HIGH
        if low_score >= 2 or word_count < 30:
            return TaskComplexity.LOW
        return TaskComplexity.MEDIUM

    def estimate_tokens(self, text: str) -> int:
        return int(len(text.split()) * 1.3)


class ModelRouter:
    def __init__(self, llm_manager: LLMManager, local_only: bool = False):
        self.llm = llm_manager
        self.analyzer = QueryAnalyzer()
        self.local_only = local_only

    def route(self, query: str, force_local: bool = False, force_cloud: bool = False) -> RoutingDecision:
        if self.local_only or force_local:
            return RoutingDecision(
                target=RouteTarget.LOCAL,
                complexity=self.analyzer.estimate_complexity(query),
                reason="local_only_mode",
                privacy_flag=self.analyzer.detect_pii(query),
                estimated_tokens=self.analyzer.estimate_tokens(query),
            )

        if force_cloud:
            return RoutingDecision(
                target=RouteTarget.CLOUD,
                complexity=self.analyzer.estimate_complexity(query),
                reason="cloud_only_mode",
                privacy_flag=self.analyzer.detect_pii(query),
                estimated_tokens=self.analyzer.estimate_tokens(query),
            )

        has_pii = self.analyzer.detect_pii(query)
        if has_pii:
            return RoutingDecision(
                target=RouteTarget.LOCAL,
                complexity=self.analyzer.estimate_complexity(query),
                reason="pii_detected",
                privacy_flag=True,
                estimated_tokens=self.analyzer.estimate_tokens(query),
            )

        complexity = self.analyzer.estimate_complexity(query)
        if complexity == TaskComplexity.HIGH:
            return RoutingDecision(
                target=RouteTarget.CLOUD,
                complexity=complexity,
                reason="high_complexity_task",
                estimated_tokens=self.analyzer.estimate_tokens(query),
            )

        if complexity == TaskComplexity.LOW:
            return RoutingDecision(
                target=RouteTarget.LOCAL,
                complexity=complexity,
                reason="low_complexity_local_efficient",
                estimated_tokens=self.analyzer.estimate_tokens(query),
            )

        return RoutingDecision(
            target=RouteTarget.CLOUD,
            complexity=complexity,
            reason="medium_complexity_cloud_quality",
            estimated_tokens=self.analyzer.estimate_tokens(query),
        )

    async def generate(
        self, messages: list[dict], force_local: bool = False, force_cloud: bool = False, **kwargs
    ) -> tuple[LLMResponse, RoutingDecision]:
        query = messages[-1].get("content", "") if messages else ""
        decision = self.route(query, force_local, force_cloud)
        response = await self.llm.generate(
            messages, provider=decision.target.value, **kwargs
        )
        return response, decision

    async def stream(
        self, messages: list[dict], force_local: bool = False, force_cloud: bool = False, **kwargs
    ):
        query = messages[-1].get("content", "") if messages else ""
        decision = self.route(query, force_local, force_cloud)
        async for token in self.llm.stream(
            messages, provider=decision.target.value, **kwargs
        ):
            yield token

    def set_local_only(self, enabled: bool):
        self.local_only = enabled
