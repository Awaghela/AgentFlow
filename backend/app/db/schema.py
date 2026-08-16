"""
Table creation, kept deliberately backend-aware so a resolved tfidf
deployment never needs the pgvector extension at all.

`document_embeddings` uses a `vector` column type (from the pgvector
extension). If we ran a single unconditional `Base.metadata.create_all()`,
every deployment — including the default tfidf one — would need `CREATE
EXTENSION vector` to succeed, which isn't guaranteed on every Postgres
provider. So: tfidf-mode create_all explicitly excludes that one table,
and the extension is only ever created when a dense backend is active.
"""
import logging

from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.core.config import get_settings
from app.db.base import Base

logger = logging.getLogger(__name__)


def create_all_tables(engine: Engine) -> None:
    settings = get_settings()
    resolved_backend = settings.resolved_embedding_backend

    if resolved_backend in ("local", "cohere"):
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        logger.info("pgvector extension ensured (resolved_embedding_backend=%s)", resolved_backend)
        Base.metadata.create_all(bind=engine)
    else:
        tables = [t for t in Base.metadata.sorted_tables if t.name != "document_embeddings"]
        Base.metadata.create_all(bind=engine, tables=tables)
