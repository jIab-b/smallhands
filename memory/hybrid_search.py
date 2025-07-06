"""Hybrid search pipeline with BM25 and semantic strategies."""

from typing import Any, List, Tuple, Dict
from abc import ABC, abstractmethod
from rank_bm25 import BM25Okapi

class RetrievalStrategy(ABC):
    @abstractmethod
    def index(self, docs: List[str]) -> None:
        ...

    @abstractmethod
    def search(self, query: str, top_k: int) -> List[Tuple[str, float]]:
        ...

class BM25Strategy(RetrievalStrategy):
    def __init__(self):
        self.bm25 = None
        self.docs: List[str] = []

    def index(self, docs: List[str]) -> None:
        tokenized = [doc.split() for doc in docs]
        self.bm25 = BM25Okapi(tokenized)
        self.docs = docs

    def search(self, query: str, top_k: int) -> List[Tuple[str, float]]:
        if not self.bm25:
            return []
        tokenized_query = query.split()
        scores = self.bm25.get_scores(tokenized_query)
        results = [(self.docs[i], float(scores[i])) for i in range(len(self.docs)) if scores[i] > 0]
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

class EmbeddingStrategy(RetrievalStrategy):
    def __init__(self, vector_store: Any):
        self.vector_store = vector_store

    def index(self, docs: List[str]) -> None:
        self.vector_store.build_index(docs)

    def search(self, query: str, top_k: int) -> List[Tuple[str, float]]:
        results = self.vector_store.search(query, top_k)
        scored = []
        for doc, dist in results:
            sim = 1.0 / (1.0 + dist)
            scored.append((doc, sim))
        return scored

class HybridSearch:
    """Hybrid search combining multiple retrieval strategies."""
    def __init__(self, strategies: Dict[str, RetrievalStrategy] = None,
                 weights: Dict[str, float] = None):
        if strategies:
            self.strategies = strategies
        else:
            from .vector_store import FaissVectorStore
            self.strategies = {
                "bm25": BM25Strategy(),
                "semantic": EmbeddingStrategy(FaissVectorStore()),
            }
        total = len(self.strategies)
        if weights:
            self.weights = weights
        else:
            self.weights = {name: 1 / total for name in self.strategies}

    def register_strategy(self, name: str, strategy: RetrievalStrategy,
                          weight: float = None) -> None:
        self.strategies[name] = strategy
        self.weights[name] = weight if weight is not None else 1.0
        total = sum(self.weights.values())
        for key in self.weights:
            self.weights[key] /= total

    def index(self, docs: List[str]) -> None:
        for strat in self.strategies.values():
            strat.index(docs)

    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        scores: Dict[str, float] = {}
        for name, strat in self.strategies.items():
            subs = strat.search(query, top_k * 2)
            weight = self.weights.get(name, 1.0)
            for doc, score in subs:
                scores[doc] = scores.get(doc, 0.0) + weight * score
        results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return results[:top_k]
