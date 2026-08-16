from __future__ import annotations

import numpy as np

from app.rag.corpus import Document
from app.rag.corpus_loader import get_active_corpus
from app.rag.embeddings import Embedder, cosine_similarity


class VectorStore:
    """
    In-process TF-IDF vector index — the EMBEDDING_BACKEND=tfidf path.

    Deliberately kept in-memory and dependency-free: this is the offline,
    deterministic fallback that requires no database round-trip, no model
    download, and no API key, and it's what the eval suite runs against so
    results stay reproducible. Real dense embeddings backed by Postgres
    live in `pgvector_store.py` (EMBEDDING_BACKEND=local or cohere) — this
    class is intentionally left untouched by that addition.
    """

    def __init__(self, documents: list[Document] | None = None) -> None:
        self.documents = documents or get_active_corpus()
        self.embedder = Embedder()
        self._matrix: np.ndarray | None = None
        self._build()

    def _build(self) -> None:
        texts = [f"{d.title}. {d.text}" for d in self.documents]
        self.embedder.fit(texts)
        self._matrix = self.embedder.encode(texts)

    def search(self, query: str, top_k: int = 4) -> list[tuple[Document, float]]:
        assert self._matrix is not None
        query_vec = self.embedder.encode([query])[0]
        scores = cosine_similarity(query_vec, self._matrix)
        order = np.argsort(-scores)[:top_k]
        return [(self.documents[i], float(scores[i])) for i in order]


_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
