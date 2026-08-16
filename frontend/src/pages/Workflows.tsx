import { useState } from "react";
import { api } from "@/api/client";
import { useAsync } from "@/hooks/useAsync";
import { TopBar } from "@/components/layout/TopBar";
import { Panel } from "@/components/common/Panel";
import { Loading, ErrorState } from "@/components/common/Loading";
import { EmptyState } from "@/components/common/Loading";
import { WorkflowRow } from "@/components/workflows/WorkflowRow";
import { NewRequestForm } from "@/components/workflows/NewRequestForm";
import clsx from "clsx";

const FILTERS = [
  { label: "All", value: undefined },
  { label: "Completed", value: "completed" },
  { label: "Pending approval", value: "pending_approval" },
  { label: "Fallback", value: "fallback" },
  { label: "Rejected", value: "rejected" },
];

export function Workflows() {
  const [status, setStatus] = useState<string | undefined>(undefined);
  const [includeEval, setIncludeEval] = useState(true);

  const { data, loading, error, refetch } = useAsync(
    () => api.listWorkflows({ status, is_eval: includeEval ? undefined : false, limit: 50 }),
    [status, includeEval]
  );

  return (
    <>
      <TopBar title="Workflow runs" description="Every request the platform has planned, executed, and traced." />
      <div className="px-8 py-6">
        <div className="mb-6">
          <Panel eyebrow="Submit a request" title="New agent workflow">
            <NewRequestForm />
          </Panel>
        </div>

        <Panel
          eyebrow={data ? `${data.total} total` : undefined}
          title="Runs"
          action={
            <div className="flex items-center gap-3">
              <label className="flex items-center gap-1.5 font-mono text-[11px] text-text-secondary">
                <input
                  type="checkbox"
                  checked={includeEval}
                  onChange={(e) => setIncludeEval(e.target.checked)}
                  className="accent-signal-amber"
                />
                include eval runs
              </label>
              <div className="flex gap-1">
                {FILTERS.map((f) => (
                  <button
                    key={f.label}
                    onClick={() => setStatus(f.value)}
                    className={clsx(
                      "rounded-sm border px-2.5 py-1 font-mono text-[10px] uppercase tracking-wide transition-colors",
                      status === f.value
                        ? "border-signal-amber/40 bg-signal-amberSoft text-signal-amber"
                        : "border-border text-text-faint hover:text-text-secondary"
                    )}
                  >
                    {f.label}
                  </button>
                ))}
              </div>
            </div>
          }
        >
          {loading && <Loading label="Loading runs" />}
          {error && <ErrorState message={error} onRetry={refetch} />}
          {data && data.items.length === 0 && (
            <EmptyState title="No runs match this filter" description="Submit a request above or clear the filter." />
          )}
          {data && data.items.length > 0 && (
            <div className="flex flex-col">
              {data.items.map((run) => (
                <WorkflowRow key={run.id} run={run} />
              ))}
            </div>
          )}
        </Panel>
      </div>
    </>
  );
}
