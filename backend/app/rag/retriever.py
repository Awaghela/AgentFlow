from __future__ import annotations

import logging
from dataclasses import dataclass

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    query: str
    doc_ids: list[str]
    snippets: list[str]
    top_score: float
    avg_score: float
    num_results: int
    reranked: bool = False  # True only if a rerank call genuinely succeeded
    candidates_considered: int = 0  # first-stage pool size before rerank narrowed it


def retrieve_context(query: str, top_k: int | None = None) -> RetrievalResult:
    settings = get_settings()
    k = top_k or settings.RETRIEVAL_TOP_K
    rerank_active = settings.resolved_rerank_provider == "cohere"
    # When reranking, fetch a larger first-stage candidate pool — reranking
    # a pool the same size as the final result count has nothing meaningful
    # to improve.
    fetch_k = settings.RERANK_CANDIDATE_POOL if rerank_active else k

    resolved_backend = settings.resolved_embedding_backend
    if resolved_backend in ("local", "cohere"):
        try:
            hits = _retrieve_via_pgvector(query, fetch_k)
        except Exception:
            # A misconfigured or unreachable dense backend (missing
            # dependency, bad API key, network blip calling Cohere) is
            # exactly the kind of failure this platform is built to survive
            # without crashing a business request. Treat it the same as
            # "no relevant context found" — empty retrieval — and let the
            # existing missing-context -> fallback -> approval path handle
            # it, instead of raising and taking the whole workflow down.
            logger.exception(
                "pgvector retrieval failed (resolved_embedding_backend=%s); "
                "degrading to empty retrieval instead of failing the request.",
                resolved_backend,
            )
            hits = []
    else:
        hits = _retrieve_via_tfidf(query, fetch_k)

    candidates_considered = len(hits)
    reranked = False
    if rerank_active and hits:
        hits, reranked = _apply_rerank(query, hits, k)
    else:
        hits = hits[:k]

    hits = [h for h in hits if h[2] >= settings.RETRIEVAL_MIN_SCORE]

    if not hits:
        return RetrievalResult(
            query=query,
            doc_ids=[],
            snippets=[],
            top_score=0.0,
            avg_score=0.0,
            num_results=0,
            reranked=reranked,
            candidates_considered=candidates_considered,
        )

    scores = [score for _, _, score in hits]
    return RetrievalResult(
        query=query,
        doc_ids=[doc_id for doc_id, _, _ in hits],
        snippets=[snippet for _, snippet, _ in hits],
        top_score=max(scores),
        avg_score=sum(scores) / len(scores),
        num_results=len(hits),
        reranked=reranked,
        candidates_considered=candidates_considered,
    )


def _apply_rerank(
    query: str, hits: list[tuple[str, str, float]], top_k: int
) -> tuple[list[tuple[str, str, float]], bool]:
    """Returns (hits, reranked) — `reranked` is False if the call failed and
    the caller silently fell back, so `retrieve_context` can report the
    truth about what actually happened rather than just "did it error"."""
    try:
        reranker = _get_cached_reranker()
        snippets = [snippet for _, snippet, _ in hits]
        ranked = reranker.rerank(query, snippets, top_n=top_k)
        return [(hits[idx][0], hits[idx][1], score) for idx, score in ranked], True
    except Exception:
        # Same resilience principle as the pgvector fallback above: a
        # broken reranker degrades to the first-stage ranking rather than
        # failing the request.
        logger.exception("Cohere rerank failed; using first-stage ranking unchanged.")
        return hits[:top_k], False


def _retrieve_via_tfidf(query: str, top_k: int) -> list[tuple[str, str, float]]:
    from app.rag.vector_store import get_vector_store

    store = get_vector_store()
    hits = store.search(query, top_k=top_k)
    return [(doc.id, f"[{doc.title}] {doc.text}", float(score)) for doc, score in hits]


def _retrieve_via_pgvector(query: str, top_k: int) -> list[tuple[str, str, float]]:
    """
    Opens its own short-lived DB session rather than threading one through
    the whole call chain (LangGraph nodes → tools → retriever) — keeps this
    an isolated, self-contained change instead of a signature change that
    ripples through every caller.
    """
    from app.db.session import SessionLocal
    from app.rag.pgvector_store import search as pgvector_search

    provider = _get_cached_provider()
    with SessionLocal() as db:
        results = pgvector_search(db, provider, query, top_k=top_k)
    return [(r.doc_id, f"[{r.title}] {r.text}", r.score) for r in results]


_cached_provider = None


def _get_cached_provider():
    # The local provider loads a model into memory; the Cohere provider
    # opens an HTTP client. Both are cheap to reuse and expensive-ish to
    # recreate per request, so cache the instance module-level, same
    # pattern as `get_vector_store()`.
    global _cached_provider
    if _cached_provider is None:
        from app.rag.embedding_providers import get_embedding_provider

        _cached_provider = get_embedding_provider()
    return _cached_provider


_cached_reranker = None


def _get_cached_reranker():
    global _cached_reranker
    if _cached_reranker is None:
        from app.rag.reranker import get_reranker

        _cached_reranker = get_reranker()
    return _cached_reranker

