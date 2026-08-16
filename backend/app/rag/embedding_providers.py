"""
Dense embedding providers for the pgvector retrieval backend.

These are only used when EMBEDDING_BACKEND is "local" or "cohere" — the
default "tfidf" backend never imports this module, so neither torch nor
the cohere SDK need to be installed/configured for the app to run.

Both providers implement the same tiny interface (`encode_documents`,
`encode_query`, `dim`) so `VectorStore` doesn't need to know which one is
active.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from app.core.config import get_settings


class EmbeddingProvider(ABC):
    dim: int

    @abstractmethod
    def encode_documents(self, texts: list[str]) -> np.ndarray:
        """Embed corpus documents for storage. Shape: (len(texts), self.dim)."""

    @abstractmethod
    def encode_query(self, text: str) -> np.ndarray:
        """Embed a single search query. Shape: (self.dim,)."""


class LocalDenseProvider(EmbeddingProvider):
    """
    Real dense embeddings via a local sentence-transformers model
    (all-MiniLM-L6-v2, 384-dim). Runs fully offline once the model weights
    are cached — no API key, no per-call cost — but needs the optional
    `requirements-local-embeddings.txt` installed (pulls in torch) and,
    on first run, network access to download the model from Hugging Face.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.dim = settings.LOCAL_EMBEDDING_DIMENSION
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "EMBEDDING_BACKEND=local requires sentence-transformers. Install with:\n"
                "  pip install -r requirements-local-embeddings.txt --break-system-packages"
            ) from exc
        self._model = SentenceTransformer(settings.LOCAL_EMBEDDING_MODEL)

    def encode_documents(self, texts: list[str]) -> np.ndarray:
        return np.asarray(self._model.encode(texts, normalize_embeddings=True))

    def encode_query(self, text: str) -> np.ndarray:
        return np.asarray(self._model.encode([text], normalize_embeddings=True))[0]


class CohereProvider(EmbeddingProvider):
    """
    Real dense embeddings via Cohere's Embed API (embed-v4.0). Cohere
    distinguishes how a text is embedded depending on whether it's a
    corpus document or a search query (`input_type="search_document"` vs
    `"search_query"`) — encoding both the same way measurably hurts
    retrieval quality, so this provider keeps that distinction rather than
    calling a single generic `.encode()`.
    """

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.COHERE_API_KEY:
            raise RuntimeError("EMBEDDING_BACKEND=cohere requires COHERE_API_KEY to be set.")

        try:
            import cohere
        except ImportError as exc:
            raise RuntimeError(
                "EMBEDDING_BACKEND=cohere requires the `cohere` package (already in requirements.txt)."
            ) from exc

        self._client = cohere.ClientV2(api_key=settings.COHERE_API_KEY)
        self._model = settings.COHERE_EMBED_MODEL
        self.dim = settings.COHERE_EMBED_DIMENSION

    def encode_documents(self, texts: list[str]) -> np.ndarray:
        response = self._client.embed(
            texts=texts,
            model=self._model,
            input_type="search_document",
            output_dimension=self.dim,
            embedding_types=["float"],
        )
        return np.asarray(response.embeddings.float_)

    def encode_query(self, text: str) -> np.ndarray:
        response = self._client.embed(
            texts=[text],
            model=self._model,
            input_type="search_query",
            output_dimension=self.dim,
            embedding_types=["float"],
        )
        return np.asarray(response.embeddings.float_)[0]


def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    resolved_backend = settings.resolved_embedding_backend
    if resolved_backend == "local":
        return LocalDenseProvider()
    if resolved_backend == "cohere":
        return CohereProvider()
    raise ValueError(
        f"get_embedding_provider() called with resolved_embedding_backend={resolved_backend!r}; "
        "only 'local' and 'cohere' have dense providers ('tfidf' uses the in-memory path directly)."
    )
