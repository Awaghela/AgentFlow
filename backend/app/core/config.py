"""
Centralized application settings.

All configuration is sourced from environment variables (with sane local
defaults) so the same image can run in dev, CI, and prod without code
changes. See `.env.example` for the full list of knobs.
"""
import json
from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Core ---
    APP_NAME: str = "AgentFlow"
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    LOG_LEVEL: str = "INFO"

    # --- CORS ---
    # Accepts either a comma-separated string (simplest for Railway/Vercel
    # dashboard env vars, e.g. "https://myapp.vercel.app,https://myapp-git-main.vercel.app")
    # or a JSON array string. Plain comma-separated is recommended in prod.
    # NOTE: kept as a raw `str` (not List[str]) because pydantic-settings
    # tries to JSON-decode List[...] env vars before any validator runs,
    # which rejects plain comma-separated values outright. See
    # `cors_origins_list` below for the parsed form.
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        v = self.CORS_ORIGINS.strip()
        if v.startswith("["):
            return json.loads(v)
        return [origin.strip() for origin in v.split(",") if origin.strip()]

    # --- Database ---
    # Accepts the raw "postgres://" / "postgresql://" URL Railway's Postgres
    # plugin (and most managed Postgres providers) hand you and rewrites it
    # to the "postgresql+psycopg://" scheme SQLAlchemy needs, so you can
    # paste Railway's DATABASE_URL reference variable in unmodified.
    DATABASE_URL: str = (
        "postgresql+psycopg://agentflow:agentflow@localhost:5432/agentflow"
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def _normalize_database_url(cls, v: object) -> object:
        if isinstance(v, str):
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+psycopg://", 1)
            if v.startswith("postgresql://") and "+psycopg" not in v:
                return v.replace("postgresql://", "postgresql+psycopg://", 1)
        return v

    # --- LLM ---
    # If unset, the orchestrator runs in deterministic SIMULATION mode:
    # every LangGraph node produces realistic, reproducible synthetic
    # output instead of calling a real model. This keeps the platform
    # fully runnable (and its 120-scenario eval suite fully reproducible)
    # with zero external dependencies. Set ANTHROPIC_API_KEY to switch
    # planning/response nodes over to live Claude calls.
    ANTHROPIC_API_KEY: str | None = None
    ANTHROPIC_MODEL: str = "claude-sonnet-4-6"
    LLM_MODE: str = "simulation"  # "simulation" | "live"

    # --- Orchestration ---
    MAX_PLAN_STEPS: int = 6
    TOOL_CALL_TIMEOUT_S: float = 8.0
    RETRIEVAL_TOP_K: int = 4
    RETRIEVAL_MIN_SCORE: float = 0.18
    AUTO_APPROVE_CONFIDENCE: float = 0.82  # >= this, skip human approval
    FALLBACK_MAX_RETRIES: int = 2

    # --- Retrieval / embedding backend ---
    # "auto"   (default) — use Cohere automatically if COHERE_API_KEY is set,
    #           otherwise fall back to tfidf. This means simply adding a
    #           Cohere key to .env is enough to switch retrieval over to
    #           real embeddings — no separate flag to remember.
    # "tfidf"  — force in-memory TF-IDF + cosine similarity, zero external
    #           dependencies, zero DB round-trips, fully deterministic —
    #           explicitly overrides auto-detection even if a Cohere key is
    #           present. The eval suite and test suite force this (see
    #           `resolved_embedding_backend` below) so they stay
    #           reproducible and don't spend live API quota regardless of
    #           what's in your environment.
    # "local"  — force real dense embeddings via a local sentence-transformers
    #           model, stored and queried through pgvector. Offline after
    #           the model is cached, but needs `pip install -r
    #           requirements-local-embeddings.txt` first.
    # "cohere" — force real dense embeddings via Cohere's Embed API, stored
    #           and queried through pgvector. Needs COHERE_API_KEY.
    EMBEDDING_BACKEND: str = "auto"
    CORPUS_SOURCE: str = "seed"  # "seed" | "real_world" | "combined"

    COHERE_API_KEY: str | None = None
    COHERE_EMBED_MODEL: str = "embed-v4.0"
    COHERE_EMBED_DIMENSION: int = 1024  # embed-v4.0 supports 256/512/1024/1536

    LOCAL_EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    LOCAL_EMBEDDING_DIMENSION: int = 384  # fixed by the MiniLM model architecture

    @property
    def resolved_embedding_backend(self) -> str:
        """
        The actual backend to use, after resolving "auto". Every call site
        in the app reads this — never the raw EMBEDDING_BACKEND field
        directly — so "auto" only has to be handled in one place.
        """
        if self.EMBEDDING_BACKEND != "auto":
            return self.EMBEDDING_BACKEND
        return "cohere" if self.COHERE_API_KEY else "tfidf"

    @property
    def embedding_dimension(self) -> int:
        """Active dense-vector dimension for the configured backend — used to
        size the pgvector column. Irrelevant when resolved_embedding_backend
        is tfidf."""
        return {
            "cohere": self.COHERE_EMBED_DIMENSION,
            "local": self.LOCAL_EMBEDDING_DIMENSION,
        }.get(self.resolved_embedding_backend, self.COHERE_EMBED_DIMENSION)

    # --- Reranking (second-stage relevance refinement) ---
    # "auto"   (default) — use Cohere Rerank automatically if COHERE_API_KEY
    #           is set, otherwise skip reranking. Same auto-detection
    #           pattern as EMBEDDING_BACKEND: adding a Cohere key is enough,
    #           no separate flag needed.
    # "none"   — force no reranking, even if a Cohere key is present.
    # "cohere" — force reranking on. After first-stage retrieval (TF-IDF
    #           *or* pgvector — reranking only needs the candidate
    #           documents' text, not whichever embedding produced them)
    #           returns a larger candidate pool, Cohere's Rerank API
    #           re-scores those candidates for precision and narrows to the
    #           final RETRIEVAL_TOP_K. Needs COHERE_API_KEY.
    #           A failed rerank call (bad key, network, rate limit) falls back
    #           to the first-stage ranking unchanged — reranking is a quality
    #           improvement, never a hard dependency for a request to succeed.
    RERANK_PROVIDER: str = "auto"
    COHERE_RERANK_MODEL: str = "rerank-v3.5"
    RERANK_CANDIDATE_POOL: int = 10  # first-stage results fetched before reranking narrows down

    @property
    def resolved_rerank_provider(self) -> str:
        """The actual rerank provider to use, after resolving "auto"."""
        if self.RERANK_PROVIDER != "auto":
            return self.RERANK_PROVIDER
        return "cohere" if self.COHERE_API_KEY else "none"

    # --- Eval harness ---
    EVAL_SCENARIO_COUNT: int = 120
    EVAL_SEED: int = 42


@lru_cache
def get_settings() -> Settings:
    return Settings()
