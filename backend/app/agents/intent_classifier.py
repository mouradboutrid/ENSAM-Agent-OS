"""
Embedding-Based Capability Router using Exemplars.

Uses a local, lightweight multilingual sentence-transformer model (sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)
to calculate cosine similarity between user queries and class exemplars for each agent.
Runs fully locally on CPU in ~5-15ms.
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    intent: str
    confidence: float
    scores: dict[str, float]
    method: str


class IntentClassifier:
    """Dynamic agent capability router based on semantic similarity of agent exemplars."""

    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        self._model_name = model_name
        self._tokenizer = None
        self._model = None
        self._agent_exemplars: dict[str, list[list[float]]] = {}
        self._fallbacks = {
            "admin": ["schedule", "grade", "exam", "note", "horaire", "salle", "inscription", "examen", "timetable", "my grade"],
            "orientation": ["career", "carrière", "orientation", "métier", "job", "stage", "internship"],
            "synthesis": ["summarize", "résumé", "report", "synthèse", "compare", "guide"],
        }
        logger.info(f"Exemplar Capability Router initialized with model={model_name}")

    def _load_model(self):
        if self._model is not None:
            return
        logger.info(f"Loading local embedding model: {self._model_name}...")
        try:
            from transformers import AutoTokenizer, AutoModel
            self._tokenizer = AutoTokenizer.from_pretrained(self._model_name)
            self._model = AutoModel.from_pretrained(self._model_name)
            self._model.eval()
            logger.info("Local embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise e

    def _mean_pooling(self, model_output, attention_mask):
        import torch
        token_embeddings = model_output[0]
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

    def _get_embedding(self, text: str) -> list[float]:
        import torch
        import torch.nn.functional as F

        if not self._tokenizer or not self._model:
            raise RuntimeError("Embedding model is not loaded")

        encoded_input = self._tokenizer(
            text, padding=True, truncation=True, max_length=512, return_tensors='pt'
        )
        with torch.no_grad():
            model_output = self._model(**encoded_input)

        sentence_embeddings = self._mean_pooling(model_output, encoded_input['attention_mask'])
        sentence_embeddings = F.normalize(sentence_embeddings, p=2, dim=1)
        return sentence_embeddings[0].tolist()

    def register_agents(self, agents_map: dict):
        """Dynamically register agents and precompute their exemplar embeddings."""
        logger.info(f"Registering {len(agents_map)} agents for semantic routing...")
        
        try:
            self._load_model()
            for agent_id, agent in agents_map.items():
                exemplars = []
                if hasattr(agent, "get_exemplars"):
                    exemplars = agent.get_exemplars()
                
                # If no exemplars defined, use capability description
                if not exemplars:
                    cap = agent.get_capability()
                    exemplars = [f"{cap.name}: {cap.description}"]
                
                self._agent_exemplars[agent_id] = []
                for ex in exemplars:
                    emb = self._get_embedding(ex)
                    self._agent_exemplars[agent_id].append(emb)
                logger.info(f"Registered {len(exemplars)} exemplars for '{agent_id}' agent capability description")
        except Exception as e:
            logger.error(f"Failed to precompute agent exemplars: {e}. Router running on keyword fallback.")

    def classify(self, query: str) -> ClassificationResult:
        # If model failed to load, fall back to keyword classification
        if not self._agent_exemplars:
            fb = self._keyword_fallback(query)
            return ClassificationResult(intent=fb, confidence=0.5, scores={}, method="keyword-fallback")

        try:
            self._load_model()
            query_emb = self._get_embedding(query)
            scores: dict[str, float] = {}
            
            for agent_id, embs in self._agent_exemplars.items():
                # Take the MAX similarity score across all exemplars for this agent
                max_sim = 0.0
                for emb in embs:
                    sim = sum(q * e for q, e in zip(query_emb, emb))
                    if sim > max_sim:
                        max_sim = sim
                scores[agent_id] = float(max_sim)

            best_intent = max(scores, key=scores.get)  # type: ignore
            best_score = scores[best_intent]

            return ClassificationResult(
                intent=best_intent,
                confidence=round(best_score, 4),
                scores={k: round(v, 4) for k, v in scores.items()},
                method="embedding",
            )
        except Exception as e:
            logger.warning(f"Embedding classification failed: {e}. Falling back to keywords.")
            fb = self._keyword_fallback(query)
            return ClassificationResult(intent=fb, confidence=0.5, scores={}, method="keyword-fallback")

    def _keyword_fallback(self, query: str) -> str:
        query_lower = query.lower()
        for intent, keywords in self._fallbacks.items():
            if any(kw in query_lower for kw in keywords):
                return intent
        return "tutor"


_classifier: IntentClassifier | None = None


def get_intent_classifier() -> IntentClassifier:
    global _classifier
    if _classifier is None:
        _classifier = IntentClassifier()
    return _classifier
