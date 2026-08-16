export type WorkflowStatus =
  | "planning"
  | "retrieving"
  | "executing_tools"
  | "validating"
  | "pending_approval"
  | "approved"
  | "rejected"
  | "completed"
  | "failed"
  | "fallback";

export interface ToolCall {
  id: string;
  tool_name: string;
  arguments: Record<string, unknown> | null;
  result: unknown;
  success: boolean;
  latency_ms: number;
  error: string | null;
}

export interface RetrievalTrace {
  id: string;
  query: string;
  retrieved_doc_ids: string[];
  top_score: number;
  avg_score: number;
  num_results: number;
  reranked: boolean;
  candidates_considered: number;
}

export interface AgentStep {
  id: string;
  step_index: number;
  node_name: string;
  status: string;
  input_data: Record<string, unknown> | null;
  output_data: Record<string, unknown> | null;
  latency_ms: number;
  error: string | null;
  tool_calls: ToolCall[];
  retrieval: RetrievalTrace | null;
}

export interface Approval {
  id: string;
  reason: string;
  risk_level: "low" | "medium" | "high";
  confidence_at_request: number;
  status: "pending" | "auto_approved" | "approved" | "rejected";
  reviewer: string | null;
  decision_notes: string | null;
  decided_at: string | null;
  workflow_run: {
    id: string;
    request_text: string;
    requester: string;
    status: WorkflowStatus;
    confidence: number | null;
    latency_ms: number | null;
  };
}

export interface WorkflowRun {
  id: string;
  request_text: string;
  requester: string;
  status: WorkflowStatus;
  plan: PlanStep[] | null;
  final_output: string | null;
  confidence: number | null;
  latency_ms: number | null;
  fallback_count: number;
  error: string | null;
  is_eval: boolean;
  created_at: string;
  completed_at: string | null;
}

export interface PlanStep {
  step: number;
  action: string;
  tool?: string;
  description: string;
}

export interface WorkflowRunDetail extends WorkflowRun {
  steps: AgentStep[];
  approval: Approval | null;
}

export interface WorkflowListResponse {
  total: number;
  items: WorkflowRun[];
}

export interface LatencyPercentiles {
  p50: number;
  p90: number;
  p95: number;
  p99: number;
  avg: number;
}

export interface StatusBreakdownEntry {
  status: string;
  count: number;
}

export interface CategoryStat {
  category: string;
  total: number;
  passed: number;
  failed: number;
  pass_rate: number;
  avg_latency_ms: number;
}

export interface ApprovalStats {
  auto_approved: number;
  approved: number;
  rejected: number;
  pending: number;
  auto_approval_rate: number;
}

export interface ToolStat {
  tool_name: string;
  calls: number;
  success_rate: number;
  avg_latency_ms: number;
}

export interface OverviewMetrics {
  total_runs: number;
  completed_runs: number;
  failed_runs: number;
  fallback_runs: number;
  success_rate: number;
  fallback_rate: number;
  avg_confidence: number;
  latency: LatencyPercentiles;
  status_breakdown: StatusBreakdownEntry[];
  approvals: ApprovalStats;
  tool_stats: ToolStat[];
  eval_category_breakdown: CategoryStat[];
  eval_pass_rate: number;
  eval_scenario_count: number;
  last_eval_run_at: string | null;
}

export interface LatencyTimeseriesPoint {
  bucket: string;
  avg_latency_ms: number;
  run_count: number;
}

export interface EvalScenario {
  id: string;
  name: string;
  category: string;
  description: string;
  expected_behavior: string;
  severity: string;
}

export interface EvalResult {
  id: string;
  scenario_id: string;
  workflow_run_id: string | null;
  category: string;
  passed: boolean;
  latency_ms: number;
  failure_reason: string | null;
  assertions: string[];
}

export interface EvalRun {
  id: string;
  label: string;
  scenario_count: number;
  passed_count: number;
  failed_count: number;
  started_at: string;
  completed_at: string | null;
}

export interface EvalRunDetail extends EvalRun {
  results: EvalResult[];
}
