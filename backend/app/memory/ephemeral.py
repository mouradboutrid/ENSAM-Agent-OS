from __future__ import annotations
import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class CacheEntry:
    value: Any
    expires_at: float
    created_at: float = field(default_factory=time.time)


class EphemeralMemory:
    def __init__(self, default_ttl: int = 3600):
        self._store: dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            if time.time() > entry.expires_at:
                del self._store[key]
                return None
            return entry.value

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        async with self._lock:
            expires = time.time() + (ttl or self._default_ttl)
            self._store[key] = CacheEntry(value=value, expires_at=expires)

    async def delete(self, key: str) -> bool:
        async with self._lock:
            return self._store.pop(key, None) is not None

    async def delete_pattern(self, pattern: str) -> int:
        async with self._lock:
            keys_to_delete = [k for k in self._store if pattern in k]
            for k in keys_to_delete:
                del self._store[k]
            return len(keys_to_delete)

    async def get_session_messages(self, session_id: str) -> list[dict]:
        data = await self.get(f"session:{session_id}:messages")
        return data or []

    async def add_session_message(self, session_id: str, role: str, content: str):
        messages = await self.get_session_messages(session_id)
        messages.append({"role": role, "content": content, "timestamp": time.time()})
        await self.set(f"session:{session_id}:messages", messages)

    async def clear_session(self, session_id: str):
        await self.delete(f"session:{session_id}:messages")

    async def get_all_keys(self) -> list[str]:
        async with self._lock:
            now = time.time()
            return [k for k, v in self._store.items() if now <= v.expires_at]

    async def cleanup_expired(self):
        async with self._lock:
            now = time.time()
            expired = [k for k, v in self._store.items() if now > v.expires_at]
            for k in expired:
                del self._store[k]
            return len(expired)

    async def get_user_keys(self, user_id: str) -> list[str]:
        async with self._lock:
            return [k for k in self._store if user_id in k]

    async def delete_user_data(self, user_id: str) -> int:
        keys = await self.get_user_keys(user_id)
        count = 0
        for k in keys:
            if await self.delete(k):
                count += 1
        return count
