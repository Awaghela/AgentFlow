import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.schema import create_all_tables
from app.db.session import engine

configure_logging()
logger = logging.getLogger("agentflow")

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Enterprise agent workflow platform: translates business requests into "
        "multi-step AI plans, retrieves context, calls tools, and returns "
        "auditable recommendations with full trace logging and human approval gates."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    # Every Vercel preview deployment gets its own random subdomain
    # (my-app-git-branch-team.vercel.app, my-app-abc123.vercel.app, ...);
    # this regex covers all of them in addition to the explicit
    # production domain(s) listed in CORS_ORIGINS.
    allow_origin_regex=r"https://.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
def on_startup() -> None:
    # Ensures a fresh `docker compose up` has tables even before seed_db.py
    # runs; seed_db.py remains the source of truth for demo/eval data.
    import app.models  # noqa: F401 - register all models on Base metadata

    create_all_tables(engine)
    logger.info("%s API started (llm_mode=%s)", settings.APP_NAME, settings.LLM_MODE)


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok", "app": settings.APP_NAME, "llm_mode": settings.LLM_MODE}
