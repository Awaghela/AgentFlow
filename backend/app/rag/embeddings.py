"""
Embedding backend for the retrieval pipeline.

Uses a TF-IDF vectorizer rather than a hosted embedding API so the whole
platform — including the 120-scenario eval suite — runs deterministically
offline with zero external calls. Swapping this for a real embedding model
(OpenAI, Voyage, sentence-transformers) is a drop-in change: implement
`Embedder.encode()` against the same interface.
"""
from __future__ import annotations

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


class Embedder:
    def __init__(self) -> None:
        self._vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            max_features=4096,
        )
        self._fitted = False

    def fit(self, corpus_texts: list[str]) -> None:
        self._vectorizer.fit(corpus_texts)
        self._fitted = True

    def encode(self, texts: list[str]) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("Embedder must be fit on the corpus before use")
        matrix = self._vectorizer.transform(texts)
        return matrix.toarray()

    @property
    def fitted(self) -> bool:
        return self._fitted


def cosine_similarity(query_vec: np.ndarray, doc_matrix: np.ndarray) -> np.ndarray:
    """Row-wise cosine similarity between a single query vector and a doc matrix."""
    q_norm = np.linalg.norm(query_vec) + 1e-9
    d_norms = np.linalg.norm(doc_matrix, axis=1) + 1e-9
    dots = doc_matrix @ query_vec
    return dots / (d_norms * q_norm)
