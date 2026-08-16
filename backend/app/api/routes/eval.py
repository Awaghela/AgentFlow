from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.eval.runner import run_eval_suite
from app.models.eval import EvalRun, EvalScenario
from app.schemas.eval import (
    EvalRunDetailOut,
    EvalRunOut,
    EvalScenarioOut,
    TriggerEvalRunRequest,
)

router = APIRouter(prefix="/eval", tags=["eval"])


@router.get("/scenarios", response_model=list[EvalScenarioOut])
def list_scenarios(
    db: Session = Depends(get_db), category: str | None = Query(default=None)
) -> list[EvalScenario]:
    stmt = select(EvalScenario).order_by(EvalScenario.category, EvalScenario.name)
    if category:
        stmt = stmt.where(EvalScenario.category == category)
    return db.execute(stmt).scalars().all()


@router.get("/runs", response_model=list[EvalRunOut])
def list_eval_runs(db: Session = Depends(get_db), limit: int = Query(default=10, ge=1, le=50)) -> list[EvalRun]:
    stmt = select(EvalRun).order_by(EvalRun.started_at.desc()).limit(limit)
    return db.execute(stmt).scalars().all()


@router.get("/runs/{eval_run_id}", response_model=EvalRunDetailOut)
def get_eval_run(eval_run_id: str, db: Session = Depends(get_db)) -> EvalRun:
    stmt = (
        select(EvalRun)
        .where(EvalRun.id == eval_run_id)
        .options(selectinload(EvalRun.results))
    )
    run = db.execute(stmt).scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=404, detail="eval run not found")
    return run


@router.post("/runs", response_model=EvalRunOut, status_code=201)
def trigger_eval_run(payload: TriggerEvalRunRequest, db: Session = Depends(get_db)) -> EvalRun:
    stmt = select(EvalScenario).order_by(EvalScenario.category, EvalScenario.name)
    scenarios = db.execute(stmt).scalars().all()
    if not scenarios:
        raise HTTPException(status_code=400, detail="no scenarios seeded — run scripts/seed_db.py first")
    if payload.scenario_limit:
        scenarios = scenarios[: payload.scenario_limit]
    return run_eval_suite(db, scenarios, label=payload.label)
