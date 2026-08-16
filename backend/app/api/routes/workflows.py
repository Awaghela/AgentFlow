from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.persistence import persist_run
from app.db.session import get_db
from app.models.workflow import AgentStep, WorkflowRun
from app.orchestration.executor import execute_workflow
from app.schemas.workflow import (
    WorkflowCreateRequest,
    WorkflowListOut,
    WorkflowRunDetailOut,
    WorkflowRunOut,
)

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("", response_model=WorkflowRunDetailOut, status_code=201)
def create_workflow(payload: WorkflowCreateRequest, db: Session = Depends(get_db)) -> WorkflowRun:
    """Submit a business request; runs the full LangGraph pipeline synchronously and returns the trace."""
    final_state, total_latency_ms = execute_workflow(
        request_text=payload.request_text, requester=payload.requester
    )
    run = persist_run(db, final_state, total_latency_ms, is_eval=False)
    return _reload_with_relations(db, run.id)


@router.get("", response_model=WorkflowListOut)
def list_workflows(
    db: Session = Depends(get_db),
    status_filter: str | None = Query(default=None, alias="status"),
    is_eval: bool | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> WorkflowListOut:
    stmt = select(WorkflowRun)
    if status_filter:
        stmt = stmt.where(WorkflowRun.status == status_filter)
    if is_eval is not None:
        stmt = stmt.where(WorkflowRun.is_eval == is_eval)

    total = len(db.execute(stmt).scalars().all())
    stmt = stmt.order_by(WorkflowRun.created_at.desc()).offset(offset).limit(limit)
    items = db.execute(stmt).scalars().all()
    return WorkflowListOut(total=total, items=[WorkflowRunOut.model_validate(i) for i in items])


@router.get("/{workflow_id}", response_model=WorkflowRunDetailOut)
def get_workflow(workflow_id: str, db: Session = Depends(get_db)) -> WorkflowRun:
    return _reload_with_relations(db, workflow_id)


def _reload_with_relations(db: Session, workflow_id: str) -> WorkflowRun:
    stmt = (
        select(WorkflowRun)
        .where(WorkflowRun.id == workflow_id)
        .options(
            selectinload(WorkflowRun.steps).selectinload(AgentStep.tool_calls),
            selectinload(WorkflowRun.steps).selectinload(AgentStep.retrieval),
            selectinload(WorkflowRun.approval),
        )
    )
    run = db.execute(stmt).scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=404, detail="workflow run not found")
    return run
