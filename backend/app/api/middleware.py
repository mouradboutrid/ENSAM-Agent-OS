from __future__ import annotations
import time
import uuid
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, rpm: int = 60):
        super().__init__(app)
        self.rpm = rpm
        self._requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path.startswith("/api/"):
            client_id = request.headers.get("X-User-ID", request.client.host if request.client else "unknown")
            now = time.time()
            self._requests[client_id] = [t for t in self._requests[client_id] if now - t < 60]
            if len(self._requests[client_id]) >= self.rpm:
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            self._requests[client_id].append(now)
        return await call_next(request)


class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = (time.perf_counter() - start) * 1000
        response.headers["X-Response-Time-Ms"] = f"{elapsed:.2f}"

        # Record metrics for chat requests
        if request.url.path == "/api/chat" and request.method == "POST":
            try:
                from app.api.deps import get_metrics
                from app.observability.metrics import LatencyRecord
                import asyncio
                metrics = get_metrics()
                record = LatencyRecord(
                    request_id=getattr(request.state, "request_id", "unknown"),
                    agent_id=response.headers.get("X-Agent-ID", "unknown"),
                    total_ms=elapsed,
                    provider=response.headers.get("X-Provider", "unknown"),
                )
                asyncio.create_task(metrics.record_latency(record))
                if response.status_code >= 400:
                    asyncio.create_task(metrics.record_error())
            except Exception:
                pass

        return response

