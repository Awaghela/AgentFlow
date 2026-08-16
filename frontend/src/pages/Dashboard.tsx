import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { Activity, CheckCircle2, GitBranch, ShieldAlert } from "lucide-react";
import { api } from "@/api/client";
import { useAsync } from "@/hooks/useAsync";
import { TopBar } from "@/components/layout/TopBar";
import { Panel } from "@/components/common/Panel";
import { Loading, ErrorState } from "@/components/common/Loading";
import { MetricCard } from "@/components/metrics/MetricCard";
import { LatencyPercentileChart } from "@/components/metrics/LatencyPercentileChart";
import { LatencyTimeseriesChart } from "@/components/metrics/LatencyTimeseriesChart";
import { CategoryBreakdownChart } from "@/components/metrics/CategoryBreakdownChart";
import { StatusDonut } from "@/components/metrics/StatusDonut";
import { ToolStatsTable } from "@/components/metrics/ToolStatsTable";
import { NewRequestForm } from "@/components/workflows/NewRequestForm";
import { WorkflowRow } from "@/components/workflows/WorkflowRow";

export function Dashboard() {
  const metrics = useAsync(() => api.getOverviewMetrics(), []);
  const timeseries = useAsync(() => api.getLatencyTimeseries(), []);
  const recentRuns = useAsync(() => api.listWorkflows({ limit: 6 }), []);

  if (metrics.loading) return <Page><Loading label="Loading platform metrics" /></Page>;
  if (metrics.error || !metrics.data)
    return (
      <Page>
        <ErrorState message={metrics.error ?? "no data"} onRetry={metrics.refetch} />
      </Page>
    );

  const m = metrics.data;

  return (
    <Page>
      <div className="mb-6">
        <Panel eyebrow="Submit a request" title="New agent workflow">
          <NewRequestForm />
        </Panel>
      </div>

      <div className="mb-6 grid grid-cols-2 gap-4 md:grid-cols-4">
        <MetricCard
          label="Total runs"
          value={String(m.total_runs)}
          icon={<GitBranch size={14} />}
          trend={`${m.eval_scenario_count} from eval suite`}
        />
        <MetricCard
          label="Success rate"
          value={`${Math.round(m.success_rate * 100)}%`}
          tone={m.success_rate >= 0.7 ? "green" : "amber"}
          icon={<CheckCircle2 size={14} />}
          trend={`${m.completed_runs} completed`}
        />
        <MetricCard
          label="Fallback rate"
          value={`${Math.round(m.fallback_rate * 100)}%`}
          tone={m.fallback_rate > 0.3 ? "amber" : "neutral"}
          icon={<ShieldAlert size={14} />}
          trend={`${m.fallback_runs} degraded runs`}
        />
        <MetricCard
          label="Avg confidence"
          value={`${Math.round(m.avg_confidence * 100)}%`}
          icon={<Activity size={14} />}
          trend={`p95 latency ${m.latency.p95.toFixed(0)}ms`}
        />
      </div>

      <div className="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Panel eyebrow="Observability" title="Latency percentiles" className="lg:col-span-1">
          <LatencyPercentileChart latency={m.latency} />
        </Panel>
        <Panel eyebrow="Observability" title="Latency over time" className="lg:col-span-2">
          {timeseries.data ? (
            <LatencyTimeseriesChart points={timeseries.data.points} />
          ) : (
            <Loading label="Loading timeseries" />
          )}
        </Panel>
      </div>

      <div className="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Panel
          eyebrow={`${m.eval_scenario_count} scenarios · ${Math.round(m.eval_pass_rate * 100)}% passed`}
          title="Eval suite — pass rate by category"
          className="lg:col-span-2"
          action={
            <Link to="/eval" className="font-mono text-[11px] uppercase text-signal-amber hover:underline">
              View suite →
            </Link>
          }
        >
          {m.eval_category_breakdown.length > 0 ? (
            <CategoryBreakdownChart data={m.eval_category_breakdown} />
          ) : (
            <p className="font-mono text-xs text-text-faint">
              No eval runs yet — trigger one from the Eval suite page.
            </p>
          )}
        </Panel>
        <Panel eyebrow="Run status" title="Status breakdown">
          <StatusDonut data={m.status_breakdown} />
        </Panel>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Panel eyebrow="Recent activity" title="Latest workflow runs" className="lg:col-span-2">
          {recentRuns.data && recentRuns.data.items.length > 0 ? (
            <div className="flex flex-col">
              {recentRuns.data.items.map((run) => (
                <WorkflowRow key={run.id} run={run} />
              ))}
            </div>
          ) : (
            <Loading label="Loading runs" />
          )}
          <Link
            to="/workflows"
            className="mt-3 inline-block font-mono text-[11px] uppercase text-signal-amber hover:underline"
          >
            View all runs →
          </Link>
        </Panel>

        <Panel eyebrow="Tool layer" title="Tool call performance">
          <ToolStatsTable tools={m.tool_stats} />
        </Panel>
      </div>
    </Page>
  );
}

function Page({ children }: { children: ReactNode }) {
  return (
    <>
      <TopBar
        title="Overview"
        description="Enterprise agent workflow platform — plans, retrieval, tool calls, and auditable recommendations."
      />
      <div className="px-8 py-6">{children}</div>
    </>
  );
}
