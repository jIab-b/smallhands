"""FAISS vector store for SmallHands."""

import os
import openai
import faiss
import numpy as np
from typing import List, Tuple, Any

class FaissVectorStore:
    def __init__(self, model: str = "text-embedding-ada-002"):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model = model
        self.index = None
        self.id_to_doc: List[str] = []

    def build_index(self, docs: List[str]) -> None:
        """Embed and index a list of documents."""
        embeddings: List[List[float]] = []
        for doc in docs:
            resp = openai.Embedding.create(input=doc, model=self.model)
            emb = resp["data"][0]["embedding"]
            embeddings.append(emb)
            self.id_to_doc.append(doc)
        arr = np.array(embeddings, dtype="float32")
        dim = arr.shape[1]
        self.index = faiss.IndexFlatL2(dim)
        self.index.add(arr)

    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """Embed query and return top_k (doc, distance)."""
        resp = openai.Embedding.create(input=query, model=self.model)
        q_emb = resp["data"][0]["embedding"]
        q_arr = np.array([q_emb], dtype="float32")
        distances, idxs = self.index.search(q_arr, top_k)
        results: List[Tuple[str, float]] = []
        for dist, idx in zip(distances[0], idxs[0]):
            results.append((self.id_to_doc[idx], float(dist)))
        return results
