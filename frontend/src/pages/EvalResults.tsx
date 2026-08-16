import { useState } from "react";
import { PlayCircle, Loader2 } from "lucide-react";
import clsx from "clsx";
import { api } from "@/api/client";
import { useAsync } from "@/hooks/useAsync";
import { TopBar } from "@/components/layout/TopBar";
import { Panel } from "@/components/common/Panel";
import { Loading, ErrorState } from "@/components/common/Loading";
import { CategoryBreakdownChart } from "@/components/metrics/CategoryBreakdownChart";
import { MetricCard } from "@/components/metrics/MetricCard";
import { ScenarioRow } from "@/components/eval/ScenarioRow";
import type { EvalResult } from "@/types";

const CATEGORY_LABELS: Record<string, string> = {
  missing_context: "Missing context",
  failed_tool_calls: "Failed tool calls",
  incorrect_retrieval: "Incorrect retrieval",
  unsafe_outputs: "Unsafe outputs",
  latency_issues: "Latency issues",
  approval_routing: "Approval routing",
  fallback_behavior: "Fallback behavior",
};

export function EvalResults() {
  const [category, setCategory] = useState<string | undefined>(undefined);
  const [running, setRunning] = useState(false);

  const metrics = useAsync(() => api.getOverviewMetrics(), []);
  const scenarios = useAsync(() => api.listEvalScenarios(category), [category]);
  const runs = useAsync(() => api.listEvalRuns(5), []);

  const latestRunId = runs.data?.[0]?.id;
  const latestRunDetail = useAsync(
    () => (latestRunId ? api.getEvalRun(latestRunId) : Promise.resolve(null)),
    [latestRunId]
  );

  const resultsByScenario = new Map<string, EvalResult>();
  latestRunDetail.data?.results.forEach((r) => resultsByScenario.set(r.scenario_id, r));

  async function triggerRun() {
    setRunning(true);
    try {
      await api.triggerEvalRun(`manual run — ${new Date().toLocaleTimeString()}`);
      metrics.refetch();
      runs.refetch();
    } finally {
      setRunning(false);
    }
  }

  return (
    <>
      <TopBar
        title="Eval suite"
        description="120 scenarios across seven failure categories, validated against the live orchestration graph."
        action={
          <button
            onClick={triggerRun}
            disabled={running}
            className="flex items-center gap-2 rounded-sm border border-signal-amber/40 bg-signal-amberSoft px-4 py-2 font-mono text-xs uppercase tracking-wide text-signal-amber transition-opacity hover:opacity-80 disabled:opacity-40"
          >
            {running ? <Loader2 size={14} className="animate-spin" /> : <PlayCircle size={14} />}
            {running ? "Running…" : "Run full suite"}
          </button>
        }
      />
      <div className="px-8 py-6">
        {metrics.loading ? (
          <Loading label="Loading eval metrics" />
        ) : metrics.error || !metrics.data ? (
          <ErrorState message={metrics.error ?? "no data"} onRetry={metrics.refetch} />
        ) : (
          <>
            <div className="mb-6 grid grid-cols-2 gap-4 md:grid-cols-4">
              <MetricCard label="Scenarios" value={String(metrics.data.eval_scenario_count)} />
              <MetricCard
                label="Pass rate"
                value={`${Math.round(metrics.data.eval_pass_rate * 100)}%`}
                tone={metrics.data.eval_pass_rate === 1 ? "green" : "amber"}
              />
              <MetricCard label="Categories" value={String(metrics.data.eval_category_breakdown.length)} />
              <MetricCard
                label="Last run"
                value={
                  metrics.data.last_eval_run_at
                    ? new Date(metrics.data.last_eval_run_at).toLocaleDateString()
                    : "—"
                }
              />
            </div>

            <div className="mb-6">
              <Panel eyebrow="Suite results" title="Pass rate by category">
                <CategoryBreakdownChart data={metrics.data.eval_category_breakdown} />
              </Panel>
            </div>
          </>
        )}

        <Panel
          eyebrow="Scenario browser"
          title="All scenarios"
          action={
            <div className="flex flex-wrap gap-1">
              <FilterChip label="All" active={category === undefined} onClick={() => setCategory(undefined)} />
              {Object.entries(CATEGORY_LABELS).map(([key, label]) => (
                <FilterChip key={key} label={label} active={category === key} onClick={() => setCategory(key)} />
              ))}
            </div>
          }
        >
          {scenarios.loading && <Loading label="Loading scenarios" />}
          {scenarios.error && <ErrorState message={scenarios.error} onRetry={scenarios.refetch} />}
          {scenarios.data && (
            <div className="flex flex-col">
              {scenarios.data.map((s) => (
                <ScenarioRow key={s.id} scenario={s} result={resultsByScenario.get(s.id)} />
              ))}
            </div>
          )}
        </Panel>
      </div>
    </>
  );
}

function FilterChip({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={clsx(
        "rounded-sm border px-2 py-1 font-mono text-[10px] uppercase tracking-wide transition-colors",
        active
          ? "border-signal-amber/40 bg-signal-amberSoft text-signal-amber"
          : "border-border text-text-faint hover:text-text-secondary"
      )}
    >
      {label}
    </button>
  );
}
