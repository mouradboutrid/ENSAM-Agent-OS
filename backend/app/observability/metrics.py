from __future__ import annotations
import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

import psutil


@dataclass
class LatencyRecord:
    request_id: str
    agent_id: str
    total_ms: float
    ttft_ms: float = 0.0
    provider: str = ""
    timestamp: float = field(default_factory=time.time)


class MetricsCollector:
    def __init__(self, window_size: int = 1000):
        self._latency_records: deque[LatencyRecord] = deque(maxlen=window_size)
        self._request_count = 0
        self._error_count = 0
        self._lock = asyncio.Lock()

    async def record_latency(self, record: LatencyRecord):
        async with self._lock:
            self._latency_records.append(record)
            self._request_count += 1

    async def record_error(self):
        async with self._lock:
            self._error_count += 1

    def get_latency_stats(self) -> dict:
        if not self._latency_records:
            return {"avg_ms": 0, "p50_ms": 0, "p95_ms": 0, "p99_ms": 0, "min_ms": 0, "max_ms": 0}
        latencies = sorted([r.total_ms for r in self._latency_records])
        n = len(latencies)
        return {
            "avg_ms": sum(latencies) / n,
            "p50_ms": latencies[n // 2],
            "p95_ms": latencies[int(n * 0.95)] if n > 1 else latencies[0],
            "p99_ms": latencies[int(n * 0.99)] if n > 1 else latencies[0],
            "min_ms": latencies[0],
            "max_ms": latencies[-1],
            "count": n,
        }

    def get_provider_latency(self) -> dict:
        providers = {}
        for r in self._latency_records:
            if r.provider not in providers:
                providers[r.provider] = []
            providers[r.provider].append(r.total_ms)
        return {
            p: {"avg_ms": sum(ls) / len(ls), "count": len(ls), "min_ms": min(ls), "max_ms": max(ls)}
            for p, ls in providers.items()
        }

    def get_system_resources(self) -> dict:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        result = {
            "cpu_percent": cpu_percent,
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "memory_percent": memory.percent,
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_percent": round(disk.percent, 1),
        }
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                result["gpu_name"] = gpu.name
                result["gpu_load_percent"] = round(gpu.load * 100, 1)
                result["gpu_memory_used_mb"] = round(gpu.memoryUsed, 1)
                result["gpu_memory_total_mb"] = round(gpu.memoryTotal, 1)
        except ImportError:
            result["gpu_available"] = False
        return result

    def get_summary(self) -> dict:
        return {
            "total_requests": self._request_count,
            "total_errors": self._error_count,
            "error_rate": self._error_count / max(self._request_count, 1),
            "latency": self.get_latency_stats(),
            "resources": self.get_system_resources(),
        }

    def get_recent_latencies(self, limit: int = 50) -> list[dict]:
        records = list(self._latency_records)[-limit:]
        return [
            {"request_id": r.request_id, "agent_id": r.agent_id, "total_ms": r.total_ms, "provider": r.provider, "timestamp": r.timestamp}
            for r in records
        ]
