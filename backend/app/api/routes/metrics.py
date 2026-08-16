from __future__ import annotations

from collections import defaultdict

import numpy as np
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.approval import ApprovalRequest, ApprovalStatus
from app.models.eval import EvalResult, EvalRun
from app.models.workflow import ToolCall, WorkflowRun, WorkflowStatus
from app.schemas.metrics import (
    ApprovalStats,
    CategoryStat,
    LatencyPercentiles,
    LatencyTimeseries,
    LatencyTimeseriesPoint,
    OverviewMetrics,
    StatusBreakdown,
    ToolStat,
)

router = APIRouter(prefix="/metrics", tags=["metrics"])


def _percentiles(values: list[float]) -> LatencyPercentiles:
    if not values:
        return LatencyPercentiles(p50=0, p90=0, p95=0, p99=0, avg=0)
    arr = np.array(values)
    return LatencyPercentiles(
        p50=round(float(np.percentile(arr, 50)), 2),
        p90=round(float(np.percentile(arr, 90)), 2),
        p95=round(float(np.percentile(arr, 95)), 2),
        p99=round(float(np.percentile(arr, 99)), 2),
        avg=round(float(np.mean(arr)), 2),
    )


@router.get("/overview", response_model=OverviewMetrics)
def overview(db: Session = Depends(get_db)) -> OverviewMetrics:
    runs = db.execute(select(WorkflowRun)).scalars().all()
    total_runs = len(runs)
    completed = [r for r in runs if r.status == WorkflowStatus.COMPLETED]
    failed = [r for r in runs if r.status == WorkflowStatus.FAILED]
    fallback = [r for r in runs if r.fallback_count and r.fallback_count > 0]
    latencies = [r.latency_ms for r in runs if r.latency_ms is not None]
    confidences = [r.confidence for r in runs if r.confidence is not None]

    status_counts: dict[str, int] = defaultdict(int)
    for r in runs:
        status_counts[r.status.value if hasattr(r.status, "value") else str(r.status)] += 1

    approvals = db.execute(select(ApprovalRequest)).scalars().all()
    approval_counts = {s: 0 for s in ["pending", "auto_approved", "approved", "rejected"]}
    for a in approvals:
        key = a.status.value if hasattr(a.status, "value") else str(a.status)
        approval_counts[key] = approval_counts.get(key, 0) + 1
    total_approvals = max(1, len(approvals))

    tool_calls = db.execute(select(ToolCall)).scalars().all()
    tool_groups: dict[str, list[ToolCall]] = defaultdict(list)
    for tc in tool_calls:
        tool_groups[tc.tool_name].append(tc)
    tool_stats = [
        ToolStat(
            tool_name=name,
            calls=len(calls),
            success_rate=round(sum(1 for c in calls if c.success) / len(calls), 4) if calls else 0.0,
            avg_latency_ms=round(sum(c.latency_ms for c in calls) / len(calls), 2) if calls else 0.0,
        )
        for name, calls in sorted(tool_groups.items())
    ]

    latest_eval_run = db.execute(
        select(EvalRun).order_by(EvalRun.started_at.desc()).limit(1)
    ).scalar_one_or_none()

    eval_category_breakdown: list[CategoryStat] = []
    eval_pass_rate = 0.0
    eval_scenario_count = 0
    last_eval_run_at = None

    if latest_eval_run is not None:
        results = db.execute(
            select(EvalResult).where(EvalResult.eval_run_id == latest_eval_run.id)
        ).scalars().all()
        eval_scenario_count = len(results)
        eval_pass_rate = round(latest_eval_run.passed_count / max(1, latest_eval_run.scenario_count), 4)
        last_eval_run_at = (
            latest_eval_run.completed_at.isoformat() if latest_eval_run.completed_at else None
        )

        by_category: dict[str, list[EvalResult]] = defaultdict(list)
        for res in results:
            by_category[res.category].append(res)

        for category, items in sorted(by_category.items()):
            passed = sum(1 for i in items if i.passed)
            eval_category_breakdown.append(
                CategoryStat(
                    category=category,
                    total=len(items),
                    passed=passed,
                    failed=len(items) - passed,
                    pass_rate=round(passed / len(items), 4) if items else 0.0,
                    avg_latency_ms=round(sum(i.latency_ms for i in items) / len(items), 2) if items else 0.0,
                )
            )

    return OverviewMetrics(
        total_runs=total_runs,
        completed_runs=len(completed),
        failed_runs=len(failed),
        fallback_runs=len(fallback),
        success_rate=round(len(completed) / total_runs, 4) if total_runs else 0.0,
        fallback_rate=round(len(fallback) / total_runs, 4) if total_runs else 0.0,
        avg_confidence=round(sum(confidences) / len(confidences), 4) if confidences else 0.0,
        latency=_percentiles(latencies),
        status_breakdown=[StatusBreakdown(status=k, count=v) for k, v in sorted(status_counts.items())],
        approvals=ApprovalStats(
            auto_approved=approval_counts.get("auto_approved", 0),
            approved=approval_counts.get("approved", 0),
            rejected=approval_counts.get("rejected", 0),
            pending=approval_counts.get("pending", 0),
            auto_approval_rate=round(approval_counts.get("auto_approved", 0) / total_approvals, 4),
        ),
        tool_stats=tool_stats,
        eval_category_breakdown=eval_category_breakdown,
        eval_pass_rate=eval_pass_rate,
        eval_scenario_count=eval_scenario_count,
        last_eval_run_at=last_eval_run_at,
    )


@router.get("/latency-timeseries", response_model=LatencyTimeseries)
def latency_timeseries(db: Session = Depends(get_db)) -> LatencyTimeseries:
    runs = db.execute(
        select(WorkflowRun).order_by(WorkflowRun.created_at.asc())
    ).scalars().all()

    buckets: dict[str, list[float]] = defaultdict(list)
    for r in runs:
        if r.latency_ms is None:
            continue
        bucket = r.created_at.strftime("%Y-%m-%d %H:00")
        buckets[bucket].append(r.latency_ms)

    points = [
        LatencyTimeseriesPoint(
            bucket=bucket,
            avg_latency_ms=round(sum(vals) / len(vals), 2),
            run_count=len(vals),
        )
        for bucket, vals in sorted(buckets.items())
    ]
    return LatencyTimeseries(points=points)
