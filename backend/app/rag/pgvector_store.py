"""
Real vector-store retrieval backend, backed by pgvector.

Used only when EMBEDDING_BACKEND is "local" or "cohere". Documents are
embedded once via `ingest()` (idempotent — safe to re-run, upserts by
doc_id) and stored in the `document_embeddings` table; `search()` embeds
the query with the same provider and runs a genuine cosine-distance
nearest-neighbor query in Postgres via pgvector's `<=>` operator (exposed
through SQLAlchemy as `.cosine_distance()`), not an in-memory scan.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document_embedding import DocumentEmbedding
from app.rag.corpus import Document
from app.rag.embedding_providers import EmbeddingProvider


@dataclass
class ScoredDoc:
    doc_id: str
    title: str
    category: str
    text: str
    score: float  # cosine similarity, 0..1 (higher = more similar) — same
    # convention as the TF-IDF path, even though pgvector natively returns
    # cosine *distance*, so callers don't need to know which backend ran.


def ingest(db: Session, provider: EmbeddingProvider, documents: list[Document]) -> int:
    """Embeds and upserts every document. Returns the number of rows written."""
    texts = [f"{d.title}. {d.text}" for d in documents]
    vectors = provider.encode_documents(texts)

    written = 0
    for doc, vector in zip(documents, vectors):
        existing = db.execute(
            select(DocumentEmbedding).where(DocumentEmbedding.doc_id == doc.id)
        ).scalar_one_or_none()

        if existing:
            existing.title = doc.title
            existing.category = doc.category
            existing.text = doc.text
            existing.embedding = vector.tolist()
            existing.provider = provider.__class__.__name__
        else:
            db.add(
                DocumentEmbedding(
                    doc_id=doc.id,
                    title=doc.title,
                    category=doc.category,
                    text=doc.text,
                    embedding=vector.tolist(),
                    provider=provider.__class__.__name__,
                )
            )
        written += 1

    db.commit()
    return written


def search(db: Session, provider: EmbeddingProvider, query: str, top_k: int = 4) -> list[ScoredDoc]:
    query_vector = provider.encode_query(query).tolist()

    # .cosine_distance() compiles to pgvector's `<=>` operator — an actual
    # index-accelerated (or exact, for small corpora) nearest-neighbor query
    # executed in Postgres, not a Python-side scan.
    stmt = (
        select(
            DocumentEmbedding,
            DocumentEmbedding.embedding.cosine_distance(query_vector).label("distance"),
        )
        .order_by("distance")
        .limit(top_k)
    )
    rows = db.execute(stmt).all()

    return [
        ScoredDoc(
            doc_id=row.DocumentEmbedding.doc_id,
            title=row.DocumentEmbedding.title,
            category=row.DocumentEmbedding.category,
            text=row.DocumentEmbedding.text,
            score=max(0.0, 1.0 - row.distance),  # cosine_distance = 1 - cosine_similarity
        )
        for row in rows
    ]


def count_embedded(db: Session) -> int:
    return db.execute(select(DocumentEmbedding)).scalars().all().__len__()


def ingest_active_corpus(db: Session) -> int:
    """
    Embeds and stores whichever corpus CORPUS_SOURCE points at (seed /
    real_world / combined) using whichever provider EMBEDDING_BACKEND
    points at. This is what `scripts/ingest_documents.py` and the seed
    script's optional embedding step both call — the single entry point
    for "point this at real documents and index them."
    """
    from app.core.config import get_settings
    from app.rag.corpus_loader import get_active_corpus
    from app.rag.embedding_providers import get_embedding_provider

    settings = get_settings()
    resolved_backend = settings.resolved_embedding_backend
    if resolved_backend not in ("local", "cohere"):
        raise ValueError(
            f"ingest_active_corpus() requires a resolved embedding backend of local or "
            f"cohere, got {resolved_backend!r} (tfidf has no persisted store to ingest into)."
        )

    provider = get_embedding_provider()
    documents = get_active_corpus()
    return ingest(db, provider, documents)
