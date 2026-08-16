"""
Seeds the database for a fresh AgentFlow instance:

  1. Creates all tables.
  2. Inserts the 120-scenario eval suite definitions.
  3. Runs the full eval suite once so the dashboard has real metrics on
     first load.
  4. Submits a handful of realistic "live" (non-eval) requests so the
     workflow list and trace viewer aren't empty either.

Run with:  python -m scripts.seed_db
"""
from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.persistence import persist_run
from app.db.schema import create_all_tables
from app.db.session import SessionLocal, engine
from app.eval.runner import run_eval_suite
from app.eval.scenarios import generate_all_scenarios
from app.models.eval import EvalRun, EvalScenario
from app.models.workflow import WorkflowRun
from app.orchestration.executor import execute_workflow

configure_logging()
logger = logging.getLogger("agentflow.seed")

DEMO_REQUESTS = [
    "What's the pricing for the Growth plan?",
    "Look up account acct_enterprise and summarize their plan and ARR.",
    "Calculate a refund for a $299 plan with 5 days used this period.",
    "What's our SLA response time for Sev-1 incidents?",
    "Open a support ticket to escalate a login issue for account acct_growth.",
    "Is account acct_churn_risk at risk based on their support ticket volume?",
    "What's our data retention policy after account cancellation?",
    "Summarize the enterprise onboarding checklist for a new customer.",
    "Draft a response about a security incident for account acct_enterprise.",
    "Can you check the terms for a contract exception on payment terms?",
]


def main() -> None:
    import app.models  # noqa: F401 register models

    logger.info("Creating tables...")
    create_all_tables(engine)

    db = SessionLocal()
    try:
        existing = db.query(EvalScenario).count()
        if existing == 0:
            logger.info("Seeding %d eval scenarios...", len(generate_all_scenarios()))
            scenario_defs = generate_all_scenarios()
            scenario_rows = []
            for sd in scenario_defs:
                row = EvalScenario(
                    name=sd.name,
                    category=sd.category,
                    description=sd.description,
                    expected_behavior=sd.expected_behavior,
                    severity=sd.severity,
                    seed_params={
                        "request_text": sd.request_text,
                        "forced_fault": dict(sd.forced_fault),
                        "expected": sd.expected,
                    },
                )
                db.add(row)
                scenario_rows.append(row)
            db.commit()
            for row in scenario_rows:
                db.refresh(row)
        else:
            logger.info("Eval scenarios already seeded (%d found), skipping.", existing)
            scenario_rows = db.query(EvalScenario).all()

        if db.query(EvalRun).count() == 0:
            logger.info("Running initial eval suite over %d scenarios...", len(scenario_rows))
            eval_run = run_eval_suite(db, scenario_rows, label="initial seed run")
            logger.info(
                "Eval suite complete: %d/%d passed", eval_run.passed_count, eval_run.scenario_count
            )
        else:
            logger.info("Eval runs already exist, skipping initial suite run.")

        settings = get_settings()
        resolved_backend = settings.resolved_embedding_backend
        if resolved_backend in ("local", "cohere"):
            try:
                from app.rag.pgvector_store import count_embedded, ingest_active_corpus

                if count_embedded(db) == 0:
                    logger.info("Ingesting corpus into pgvector (resolved_embedding_backend=%s)...", resolved_backend)
                    written = ingest_active_corpus(db)
                    logger.info("Ingested %d document(s) into pgvector.", written)
                else:
                    logger.info("pgvector store already populated, skipping ingest.")
            except Exception:
                logger.exception(
                    "pgvector ingest failed — retrieval will return empty results until this is "
                    "resolved (check EMBEDDING_BACKEND deps/credentials). Continuing seed without it."
                )

        if db.query(WorkflowRun).filter(WorkflowRun.is_eval.is_(False)).count() == 0:
            logger.info("Seeding %d demo live workflow runs...", len(DEMO_REQUESTS))
            settings = get_settings()
            live_cohere = (
                settings.resolved_embedding_backend == "cohere"
                or settings.resolved_rerank_provider == "cohere"
            )
            for i, req in enumerate(DEMO_REQUESTS):
                if live_cohere and i > 0:
                    time.sleep(10)
                final_state, total_latency_ms = execute_workflow(request_text=req, requester="demo-user")
                persist_run(db, final_state, total_latency_ms, is_eval=False)
        else:
            logger.info("Demo workflow runs already exist, skipping.")

        logger.info("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
