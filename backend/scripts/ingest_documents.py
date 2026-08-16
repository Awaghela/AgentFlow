"""
Embeds and indexes documents into the pgvector store.

By default, ingests whichever corpus CORPUS_SOURCE points at (seed /
real_world / combined) using whichever provider EMBEDDING_BACKEND points
at (local / cohere). This is the "point it at a real dataset" entry point:

  # Real regulatory-guidance corpus, embedded locally (no API key needed,
  # first run downloads the model — needs `pip install -r
  # requirements-local-embeddings.txt` first):
  EMBEDDING_BACKEND=local CORPUS_SOURCE=real_world python -m scripts.ingest_documents

  # Same corpus, embedded via Cohere's real Embed API:
  EMBEDDING_BACKEND=cohere COHERE_API_KEY=... CORPUS_SOURCE=real_world python -m scripts.ingest_documents

  # Your own documents: point --path at a folder of .txt/.md files —
  # each file becomes one document, filename (minus extension) becomes
  # the title, category defaults to "custom".
  EMBEDDING_BACKEND=cohere COHERE_API_KEY=... python -m scripts.ingest_documents --path ./my_docs
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.schema import create_all_tables
from app.db.session import SessionLocal, engine
from app.rag.corpus import Document
from app.rag.corpus_loader import get_active_corpus
from app.rag.embedding_providers import get_embedding_provider
from app.rag.pgvector_store import ingest

configure_logging()
logger = logging.getLogger("agentflow.ingest")


def _load_documents_from_folder(path: Path) -> list[Document]:
    docs = []
    for file in sorted(path.glob("*")):
        if file.suffix.lower() not in (".txt", ".md"):
            continue
        text = file.read_text(encoding="utf-8").strip()
        if not text:
            continue
        docs.append(
            Document(
                id=f"custom-{file.stem}",
                title=file.stem.replace("_", " ").replace("-", " ").title(),
                category="custom",
                text=text,
            )
        )
    return docs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--path",
        type=str,
        default=None,
        help="Folder of .txt/.md files to ingest instead of the built-in corpus.",
    )
    args = parser.parse_args()

    import app.models  # noqa: F401 — register models on Base metadata

    settings = get_settings()
    resolved_backend = settings.resolved_embedding_backend
    if resolved_backend not in ("local", "cohere"):
        logger.error(
            "resolved_embedding_backend=%s has no persisted vector store to ingest into. "
            "Set EMBEDDING_BACKEND=local or EMBEDDING_BACKEND=cohere (or set COHERE_API_KEY "
            "and leave EMBEDDING_BACKEND=auto) first.",
            resolved_backend,
        )
        sys.exit(1)

    logger.info("Ensuring tables exist (including document_embeddings)...")
    create_all_tables(engine)

    if args.path:
        documents = _load_documents_from_folder(Path(args.path))
        logger.info("Loaded %d document(s) from %s", len(documents), args.path)
    else:
        documents = get_active_corpus()
        logger.info(
            "Using built-in corpus (CORPUS_SOURCE=%s): %d document(s)",
            settings.CORPUS_SOURCE,
            len(documents),
        )

    if not documents:
        logger.warning("No documents to ingest.")
        return

    logger.info("Loading embedding provider (resolved_embedding_backend=%s)...", resolved_backend)
    provider = get_embedding_provider()

    db = SessionLocal()
    try:
        written = ingest(db, provider, documents)
        logger.info("Ingested %d document(s) into pgvector (dim=%d).", written, provider.dim)
    finally:
        db.close()


if __name__ == "__main__":
    main()
