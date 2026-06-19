from __future__ import annotations
import uuid
from typing import Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings


class SemanticMemory:
    def __init__(self, persist_dir: str = "./data/chromadb"):
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._documents = self._client.get_or_create_collection(
            name="documents", metadata={"hnsw:space": "cosine"}
        )
        self._user_profiles = self._client.get_or_create_collection(
            name="user_profiles", metadata={"hnsw:space": "cosine"}
        )
        self._conversations = self._client.get_or_create_collection(
            name="conversations", metadata={"hnsw:space": "cosine"}
        )

    def add_documents(
        self, texts: list[str], embeddings: list[list[float]],
        metadatas: Optional[list[dict]] = None, ids: Optional[list[str]] = None,
    ):
        doc_ids = ids or [str(uuid.uuid4()) for _ in texts]
        metas = metadatas or [{} for _ in texts]
        self._documents.add(documents=texts, embeddings=embeddings, metadatas=metas, ids=doc_ids)
        return doc_ids

    def search_documents(
        self, query_embedding: list[float], n_results: int = 5, where: Optional[dict] = None,
    ) -> dict:
        kwargs = {"query_embeddings": [query_embedding], "n_results": n_results, "include": ["documents", "metadatas", "distances"]}
        if where:
            kwargs["where"] = where
        return self._documents.query(**kwargs)

    def add_user_profile(self, user_id: str, profile_text: str, embedding: list[float], metadata: Optional[dict] = None):
        meta = metadata or {}
        meta["user_id"] = user_id
        self._user_profiles.upsert(documents=[profile_text], embeddings=[embedding], metadatas=[meta], ids=[user_id])

    def search_similar_users(self, query_embedding: list[float], n_results: int = 5) -> dict:
        return self._user_profiles.query(query_embeddings=[query_embedding], n_results=n_results, include=["documents", "metadatas", "distances"])

    def add_conversation_memory(self, session_id: str, text: str, embedding: list[float], metadata: Optional[dict] = None):
        meta = metadata or {}
        meta["session_id"] = session_id
        doc_id = f"{session_id}_{uuid.uuid4().hex[:8]}"
        self._conversations.add(documents=[text], embeddings=[embedding], metadatas=[meta], ids=[doc_id])

    def search_conversations(self, query_embedding: list[float], n_results: int = 5, user_id: Optional[str] = None) -> dict:
        kwargs = {"query_embeddings": [query_embedding], "n_results": n_results, "include": ["documents", "metadatas", "distances"]}
        if user_id:
            kwargs["where"] = {"user_id": user_id}
        return self._conversations.query(**kwargs)

    def delete_document(self, doc_id: str) -> bool:
        try:
            result = self._documents.get(ids=[doc_id], include=["metadatas"])
            if result["ids"]:
                meta = result["metadatas"][0] if result.get("metadatas") else {}
                if meta.get("system_document") == "true":
                    return False
                self._documents.delete(ids=[doc_id])
                return True
        except Exception:
            pass
        return False

    def delete_documents_by_source(self, source: str) -> int:
        try:
            results = self._documents.get(where={"source": source}, include=["metadatas"])
            if results["ids"]:
                deletable = []
                for i, doc_id in enumerate(results["ids"]):
                    meta = results["metadatas"][i] if results.get("metadatas") else {}
                    if meta.get("system_document") != "true":
                        deletable.append(doc_id)
                if deletable:
                    self._documents.delete(ids=deletable)
                return len(deletable)
        except Exception:
            pass
        return 0

    def is_source_ingested(self, source: str) -> bool:
        try:
            results = self._documents.get(where={"source": source}, include=["metadatas"])
            return bool(results["ids"])
        except Exception:
            return False

    def delete_user_data(self, user_id: str) -> dict:
        deleted = {"documents": 0, "profiles": 0, "conversations": 0}
        try:
            results = self._documents.get(where={"user_id": user_id}, include=["metadatas"])
            if results["ids"]:
                deletable = [
                    results["ids"][i] for i in range(len(results["ids"]))
                    if (results["metadatas"][i] if results.get("metadatas") else {}).get("system_document") != "true"
                ]
                if deletable:
                    self._documents.delete(ids=deletable)
                deleted["documents"] = len(deletable)
        except Exception:
            pass
        try:
            self._user_profiles.delete(ids=[user_id])
            deleted["profiles"] = 1
        except Exception:
            pass
        try:
            results = self._conversations.get(where={"user_id": user_id})
            if results["ids"]:
                self._conversations.delete(ids=results["ids"])
                deleted["conversations"] = len(results["ids"])
        except Exception:
            pass
        return deleted

    def get_collection_stats(self) -> dict:
        return {
            "documents": self._documents.count(),
            "user_profiles": self._user_profiles.count(),
            "conversations": self._conversations.count(),
        }

    def get_document_by_id(self, doc_id: str) -> Optional[dict]:
        try:
            result = self._documents.get(ids=[doc_id], include=["documents", "metadatas"])
            if result["ids"]:
                return {"id": result["ids"][0], "document": result["documents"][0], "metadata": result["metadatas"][0]}
        except Exception:
            pass
        return None

    def list_documents(self, limit: int = 100, offset: int = 0) -> dict:
        return self._documents.get(limit=limit, offset=offset, include=["documents", "metadatas"])
