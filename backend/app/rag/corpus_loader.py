from app.core.config import get_settings
from app.rag.corpus import CORPUS, Document
from app.rag.real_world_corpus import REAL_WORLD_CORPUS


def get_active_corpus() -> list[Document]:
    settings = get_settings()
    if settings.CORPUS_SOURCE == "real_world":
        return REAL_WORLD_CORPUS
    if settings.CORPUS_SOURCE == "combined":
        return CORPUS + REAL_WORLD_CORPUS
    return CORPUS  # "seed" (default)
