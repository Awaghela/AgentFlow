import type {
  EvalRun,
  EvalRunDetail,
  EvalScenario,
  LatencyTimeseriesPoint,
  OverviewMetrics,
  WorkflowListResponse,
  WorkflowRunDetail,
} from "@/types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new ApiError(res.status, body || res.statusText);
  }
  return res.json() as Promise<T>;
}

export const api = {
  getOverviewMetrics: () => request<OverviewMetrics>("/metrics/overview"),
  getLatencyTimeseries: () =>
    request<{ points: LatencyTimeseriesPoint[] }>("/metrics/latency-timeseries"),

  listWorkflows: (params: { status?: string; is_eval?: boolean; limit?: number; offset?: number } = {}) => {
    const qs = new URLSearchParams();
    if (params.status) qs.set("status", params.status);
    if (params.is_eval !== undefined) qs.set("is_eval", String(params.is_eval));
    if (params.limit !== undefined) qs.set("limit", String(params.limit));
    if (params.offset !== undefined) qs.set("offset", String(params.offset));
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return request<WorkflowListResponse>(`/workflows${suffix}`);
  },
  getWorkflow: (id: string) => request<WorkflowRunDetail>(`/workflows/${id}`),
  createWorkflow: (request_text: string, requester = "console-user") =>
    request<WorkflowRunDetail>("/workflows", {
      method: "POST",
      body: JSON.stringify({ request_text, requester }),
    }),

  listApprovals: (status: string = "pending") =>
    request<import("@/types").Approval[]>(`/approvals?status=${status}`),
  decideApproval: (
    id: string,
    decision: "approved" | "rejected",
    reviewer: string,
    notes?: string
  ) =>
    request<import("@/types").Approval>(`/approvals/${id}/decision`, {
      method: "POST",
      body: JSON.stringify({ decision, reviewer, notes }),
    }),

  listEvalScenarios: (category?: string) =>
    request<EvalScenario[]>(`/eval/scenarios${category ? `?category=${category}` : ""}`),
  listEvalRuns: (limit = 10) => request<EvalRun[]>(`/eval/runs?limit=${limit}`),
  getEvalRun: (id: string) => request<EvalRunDetail>(`/eval/runs/${id}`),
  triggerEvalRun: (label: string, scenario_limit?: number) =>
    request<EvalRun>("/eval/runs", {
      method: "POST",
      body: JSON.stringify({ label, scenario_limit }),
    }),
};

export { ApiError };
