from __future__ import annotations
import asyncio
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class AuditLogger:
    def __init__(self, log_dir: str = "./data/audit"):
        self._log_dir = Path(log_dir)
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._entries: list[dict] = []
        self._lock = asyncio.Lock()
        self._max_entries = 100000

    async def log(self, context, extra: Optional[dict] = None):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": getattr(context, "request_id", "unknown"),
            "session_id": getattr(context, "session_id", None),
            "user_id": getattr(context, "user_id", None),
            "agent_id": getattr(context, "agent_id", None),
            "trace": getattr(context, "trace", []),
        }
        if hasattr(context, "routing_decision") and context.routing_decision:
            rd = context.routing_decision
            entry["routing"] = {"target": rd.target.value, "complexity": rd.complexity.value, "reason": rd.reason, "privacy_flag": rd.privacy_flag}
        if extra:
            entry.update(extra)
        async with self._lock:
            self._entries.append(entry)
            if len(self._entries) > self._max_entries:
                self._entries = self._entries[-self._max_entries:]

    async def log_event(self, event_type: str, data: dict, user_id: str = "system"):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            **data,
        }
        async with self._lock:
            self._entries.append(entry)

    def get_entries(self, limit: int = 100, user_id: Optional[str] = None) -> list[dict]:
        entries = self._entries
        if user_id:
            entries = [e for e in entries if e.get("user_id") == user_id]
        return entries[-limit:]

    async def export_json(self, filepath: Optional[str] = None) -> str:
        if filepath is None:
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filepath = str(self._log_dir / f"audit_export_{ts}.json")
        async with self._lock:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self._entries, f, ensure_ascii=False, indent=2)
        return filepath

    def get_stats(self) -> dict:
        return {
            "total_entries": len(self._entries),
            "unique_users": len(set(e.get("user_id", "unknown") for e in self._entries)),
            "unique_sessions": len(set(e.get("session_id") for e in self._entries if e.get("session_id"))),
        }
