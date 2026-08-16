"""
Cohere Rerank integration.

A second-stage relevance pass over whatever the first-stage retriever
(TF-IDF or pgvector) already returned — independent of EMBEDDING_BACKEND,
since reranking only needs the candidate documents' raw text, not whatever
produced them. This mirrors a common real-world RAG pattern: cheap/fast
first-stage retrieval for recall, a neural reranker for precision.

Only used when RERANK_PROVIDER=cohere. A failed call here (bad key,
network, rate limit) is caught by the caller in `retriever.py` and falls
back to the first-stage ranking unchanged — reranking is a quality
improvement layered on top, never a hard dependency for a request to
succeed.
"""
from __future__ import annotations

from app.core.config import get_settings


class CohereReranker:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.COHERE_API_KEY:
            raise RuntimeError("RERANK_PROVIDER=cohere requires COHERE_API_KEY to be set.")

        try:
            import cohere
        except ImportError as exc:
            raise RuntimeError(
                "RERANK_PROVIDER=cohere requires the `cohere` package (already in requirements.txt)."
            ) from exc

        self._client = cohere.ClientV2(api_key=settings.COHERE_API_KEY)
        self._model = settings.COHERE_RERANK_MODEL

    def rerank(self, query: str, documents: list[str], top_n: int) -> list[tuple[int, float]]:
        """
        Returns (original_index, relevance_score) pairs, best-first.
        `relevance_score` is Cohere's own 0..1 score — it replaces, not
        supplements, the first-stage retrieval score, since it's a strictly
        more accurate relevance judgment than lexical/embedding similarity
        alone.
        """
        if not documents:
            return []

        response = self._client.rerank(
            model=self._model,
            query=query,
            documents=documents,
            top_n=min(top_n, len(documents)),
        )
        return [(r.index, r.relevance_score) for r in response.results]


_cached_reranker: CohereReranker | None = None


def get_reranker() -> CohereReranker:
    global _cached_reranker
    if _cached_reranker is None:
        _cached_reranker = CohereReranker()
    return _cached_reranker
