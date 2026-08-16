from pydantic import BaseModel


class LatencyPercentiles(BaseModel):
    p50: float
    p90: float
    p95: float
    p99: float
    avg: float


class StatusBreakdown(BaseModel):
    status: str
    count: int


class CategoryStat(BaseModel):
    category: str
    total: int
    passed: int
    failed: int
    pass_rate: float
    avg_latency_ms: float


class ApprovalStats(BaseModel):
    auto_approved: int
    approved: int
    rejected: int
    pending: int
    auto_approval_rate: float


class ToolStat(BaseModel):
    tool_name: str
    calls: int
    success_rate: float
    avg_latency_ms: float


class OverviewMetrics(BaseModel):
    total_runs: int
    completed_runs: int
    failed_runs: int
    fallback_runs: int
    success_rate: float
    fallback_rate: float
    avg_confidence: float
    latency: LatencyPercentiles
    status_breakdown: list[StatusBreakdown]
    approvals: ApprovalStats
    tool_stats: list[ToolStat]
    eval_category_breakdown: list[CategoryStat]
    eval_pass_rate: float
    eval_scenario_count: int
    last_eval_run_at: str | None = None


class LatencyTimeseriesPoint(BaseModel):
    bucket: str
    avg_latency_ms: float
    run_count: int


class LatencyTimeseries(BaseModel):
    points: list[LatencyTimeseriesPoint]
