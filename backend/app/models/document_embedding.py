import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import get_settings
from app.db.base import Base, TimestampMixin


def gen_uuid() -> str:
    return str(uuid.uuid4())


class DocumentEmbedding(TimestampMixin, Base):
    """
    Real vector-store row: one per corpus document, embedded by whichever
    dense provider is active (local sentence-transformers or Cohere Embed)
    and queried via pgvector's cosine-distance operator.

    Only populated/queried when EMBEDDING_BACKEND is "local" or "cohere" —
    the default "tfidf" backend never touches this table, so a fresh
    deployment with no embedding backend configured has an empty (but
    perfectly valid) table here.

    The vector column's dimension is fixed at import time from the active
    backend's configured dimension. Postgres/pgvector requires a fixed
    dimension per column, so mixing providers within one deployment isn't
    supported — that's an intentional simplicity trade-off, not an
    oversight: switching EMBEDDING_BACKEND requires re-running the
    ingestion script, which is cheap for a corpus this size.
    """

    __tablename__ = "document_embeddings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    doc_id: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(300))
    category: Mapped[str] = mapped_column(String(64), index=True)
    text: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    provider: Mapped[str] = mapped_column(String(32))  # "local" | "cohere" — which embedded this row
    embedding: Mapped[list[float]] = mapped_column(Vector(get_settings().embedding_dimension))
