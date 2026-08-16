from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.approval import ApprovalRequest, ApprovalStatus, RiskLevel
from app.models.workflow import AgentStep, RetrievalTrace, ToolCall, WorkflowRun, WorkflowStatus
from app.orchestration.state import AgentState

_STATUS_MAP = {
    "planning": WorkflowStatus.PLANNING,
    "retrieving": WorkflowStatus.RETRIEVING,
    "executing_tools": WorkflowStatus.EXECUTING_TOOLS,
    "fallback": WorkflowStatus.FALLBACK,
    "validating": WorkflowStatus.VALIDATING,
    "pending_approval": WorkflowStatus.PENDING_APPROVAL,
    "approved": WorkflowStatus.COMPLETED,
}


def persist_run(
    db: Session,
    final_state: AgentState,
    total_latency_ms: float,
    is_eval: bool = False,
    eval_scenario_id: str | None = None,
) -> WorkflowRun:
    status_key = final_state.get("status", "approved")
    resolved_status = _STATUS_MAP.get(status_key, WorkflowStatus.COMPLETED)

    run = WorkflowRun(
        request_text=final_state["request_text"],
        requester=final_state.get("requester", "demo-user"),
        status=resolved_status,
        plan=final_state.get("plan"),
        final_output=final_state.get("final_output"),
        confidence=final_state.get("confidence"),
        latency_ms=round(total_latency_ms, 2),
        fallback_count=final_state.get("fallback_count", 0),
        error=final_state.get("error"),
        is_eval=is_eval,
        eval_scenario_id=eval_scenario_id,
        completed_at=None if resolved_status == WorkflowStatus.PENDING_APPROVAL else datetime.now(timezone.utc),
    )
    db.add(run)
    db.flush()

    for idx, event in enumerate(final_state.get("trace", [])):
        step = AgentStep(
            workflow_run_id=run.id,
            step_index=idx,
            node_name=event["node_name"],
            status=event["status"],
            input_data=event.get("input_data"),
            output_data=event.get("output_data"),
            latency_ms=event.get("latency_ms", 0.0),
            error=event.get("error"),
        )
        db.add(step)
        db.flush()

        for tc in event.get("tool_calls") or []:
            db.add(
                ToolCall(
                    agent_step_id=step.id,
                    tool_name=tc["tool_name"],
                    arguments=tc.get("arguments"),
                    result=tc.get("result"),
                    success=tc.get("success", False),
                    latency_ms=tc.get("latency_ms", 0.0),
                    error=tc.get("error"),
                )
            )

        if event.get("retrieval") is not None:
            r = event["retrieval"]
            db.add(
                RetrievalTrace(
                    agent_step_id=step.id,
                    query=r.get("query", ""),
                    retrieved_doc_ids=r.get("doc_ids", []),
                    top_score=r.get("top_score", 0.0),
                    avg_score=r.get("avg_score", 0.0),
                    num_results=r.get("num_results", 0),
                    reranked=r.get("reranked", False),
                    candidates_considered=r.get("candidates_considered", 0),
                )
            )

    if final_state.get("requires_approval"):
        risk = final_state.get("risk_level", "low")
        db.add(
            ApprovalRequest(
                workflow_run_id=run.id,
                reason=final_state.get("approval_reason") or "review required",
                risk_level=RiskLevel(risk),
                confidence_at_request=final_state.get("confidence", 0.0),
                status=ApprovalStatus.PENDING,
            )
        )
    elif resolved_status == WorkflowStatus.COMPLETED:
        db.add(
            ApprovalRequest(
                workflow_run_id=run.id,
                reason="confidence and risk within auto-approve thresholds",
                risk_level=RiskLevel(final_state.get("risk_level", "low")),
                confidence_at_request=final_state.get("confidence", 0.0),
                status=ApprovalStatus.AUTO_APPROVED,
                decided_at=datetime.now(timezone.utc),
            )
        )

    db.commit()
    db.refresh(run)
    return run
