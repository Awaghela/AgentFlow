from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.approval import ApprovalRequest, ApprovalStatus
from app.models.workflow import WorkflowRun, WorkflowStatus
from app.schemas.approval import ApprovalDecisionRequest, ApprovalWithRunOut

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("", response_model=list[ApprovalWithRunOut])
def list_approvals(
    db: Session = Depends(get_db),
    status_filter: str | None = Query(default="pending", alias="status"),
) -> list[ApprovalRequest]:
    stmt = (
        select(ApprovalRequest)
        .options(selectinload(ApprovalRequest.workflow_run))
        .order_by(ApprovalRequest.created_at.desc())
    )
    if status_filter:
        stmt = stmt.where(ApprovalRequest.status == status_filter)
    return db.execute(stmt).scalars().all()


@router.post("/{approval_id}/decision", response_model=ApprovalWithRunOut)
def decide_approval(
    approval_id: str, payload: ApprovalDecisionRequest, db: Session = Depends(get_db)
) -> ApprovalRequest:
    approval = db.get(ApprovalRequest, approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail="approval request not found")
    if approval.status != ApprovalStatus.PENDING:
        raise HTTPException(status_code=409, detail=f"approval already resolved as {approval.status}")

    approval.status = ApprovalStatus.APPROVED if payload.decision == "approved" else ApprovalStatus.REJECTED
    approval.reviewer = payload.reviewer
    approval.decision_notes = payload.notes
    approval.decided_at = datetime.now(timezone.utc)

    run = db.get(WorkflowRun, approval.workflow_run_id)
    if run is not None:
        run.status = WorkflowStatus.COMPLETED if payload.decision == "approved" else WorkflowStatus.REJECTED
        run.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(approval)
    return approval
