"""
Integration tests for the pgvector retrieval backend.

Skipped automatically unless DATABASE_URL points at a real Postgres
instance with the pgvector extension available — the rest of the suite
runs against SQLite for speed, which has no vector type at all. Run these
specifically with:

    DATABASE_URL=postgresql+psycopg://agentflow:agentflow@localhost:5432/agentflow \
    EMBEDDING_BACKEND=local \
    pytest tests/test_pgvector_store.py -v

Note EMBEDDING_BACKEND must be set at the process level (not just inside a
test) — `DocumentEmbedding.embedding`'s Vector(dim) is resolved once, at
Python import time, from whichever backend's dimension was configured
then, and can't be changed per-test afterward.

A deterministic fake embedding provider is used rather than a real model
or API call, so this test verifies the SQL/ORM plumbing (ingest, upsert,
cosine-distance ranking) is correct without needing network access to
Hugging Face or Cohere.
"""
from __future__ import annotations

import numpy as np
import pytest
from sqlalchemy import select, text

from app.core.config import get_settings
from app.db.schema import create_all_tables
from app.db.session import SessionLocal, engine
from app.models.document_embedding import DocumentEmbedding
from app.rag.corpus import Document
from app.rag.embedding_providers import EmbeddingProvider

settings = get_settings()
IS_POSTGRES = settings.DATABASE_URL.startswith("postgresql")

pytestmark = pytest.mark.skipif(
    not IS_POSTGRES,
    reason="pgvector integration tests require a real Postgres DATABASE_URL",
)


class FakeProvider(EmbeddingProvider):
    """
    Deterministic hash-based embeddings — same text always maps to the same
    vector, so ranking/ordering is testable without a real model.

    `dim` is read from the *actual* table dimension rather than hardcoded:
    `DocumentEmbedding.embedding`'s Vector(dim) is fixed at Python import
    time from whichever EMBEDDING_BACKEND env var was set when app.models
    first loaded in this process — not necessarily what's active right now
    — so the fake provider has to match that bound dimension, not invent
    its own, or pgvector correctly (and confusingly, if you don't know
    this) rejects the insert with a dimension mismatch.
    """

    def __init__(self) -> None:
        self.dim = DocumentEmbedding.__table__.c.embedding.type.dim

    def _vec(self, text: str) -> np.ndarray:
        rng = np.random.RandomState(abs(hash(text)) % (2**32))
        v = rng.rand(self.dim)
        return v / np.linalg.norm(v)

    def encode_documents(self, texts: list[str]) -> np.ndarray:
        return np.array([self._vec(t) for t in texts])

    def encode_query(self, text: str) -> np.ndarray:
        return self._vec(text)


@pytest.fixture(autouse=True)
def _pgvector_schema():
    import app.models  # noqa: F401

    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        # The embedding column's dimension is bound once, at Python import
        # time, from whatever EMBEDDING_BACKEND was active then — it can't
        # change at runtime. Drop and recreate rather than assume a table
        # left over from a previous run (possibly with a different
        # dimension) still matches this process.
        conn.execute(text("DROP TABLE IF EXISTS document_embeddings CASCADE"))
    create_all_tables(engine)
    yield


def test_ingest_and_search_ranks_exact_match_first() -> None:
    from app.rag.pgvector_store import ingest, search

    docs = [
        Document(id="pgv-refund", title="Refund Policy", category="billing", text="Refunds within 14 days are honored in full."),
        Document(id="pgv-sla", title="SLA Terms", category="contracts", text="Enterprise customers get 99.9% uptime."),
        Document(id="pgv-security", title="Security Runbook", category="security", text="Rotate API keys after a credential leak."),
    ]
    provider = FakeProvider()
    db = SessionLocal()
    try:
        written = ingest(db, provider, docs)
        assert written == 3

        results = search(db, provider, "Refund Policy. Refunds within 14 days are honored in full.", top_k=3)
        assert results[0].doc_id == "pgv-refund"
        assert results[0].score > 0.99
        assert len(results) == 3
    finally:
        db.close()


def test_ingest_is_idempotent_upsert_not_duplicate() -> None:
    from app.rag.pgvector_store import ingest
    from app.models.document_embedding import DocumentEmbedding

    docs = [Document(id="pgv-dup", title="Dup Test", category="billing", text="Some policy text.")]
    provider = FakeProvider()
    db = SessionLocal()
    try:
        ingest(db, provider, docs)
        ingest(db, provider, docs)
        rows = db.execute(
            select(DocumentEmbedding).where(DocumentEmbedding.doc_id == "pgv-dup")
        ).scalars().all()
        assert len(rows) == 1
    finally:
        db.close()


def test_retrieve_context_dispatches_to_pgvector(monkeypatch) -> None:
    """End-to-end: retrieve_context() with EMBEDDING_BACKEND=local should
    route through pgvector, not the in-memory TF-IDF path."""
    from app.rag.pgvector_store import ingest
    import app.rag.retriever as retriever_module

    docs = [Document(id="pgv-e2e", title="Refund Policy", category="billing", text="Refunds within 14 days are honored in full.")]
    provider = FakeProvider()
    db = SessionLocal()
    try:
        ingest(db, provider, docs)
    finally:
        db.close()

    monkeypatch.setenv("EMBEDDING_BACKEND", "local")
    monkeypatch.setenv("RETRIEVAL_MIN_SCORE", "0.0")  # fake embeddings won't score like real ones
    get_settings.cache_clear()
    monkeypatch.setattr(retriever_module, "_cached_provider", provider)

    try:
        result = retriever_module.retrieve_context("Refund Policy. Refunds within 14 days are honored in full.")
        assert result.num_results >= 1
        assert "pgv-e2e" in result.doc_ids
    finally:
        get_settings.cache_clear()
