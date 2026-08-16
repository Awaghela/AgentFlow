import { Link } from "react-router-dom";
import type { WorkflowRun } from "@/types";
import { StatusPill } from "@/components/common/StatusPill";

export function WorkflowRow({ run }: { run: WorkflowRun }) {
  return (
    <Link
      to={`/workflows/${run.id}`}
      className="flex items-center justify-between gap-4 border-b border-border-soft px-1 py-3 transition-colors last:border-0 hover:bg-surface-hover"
    >
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm text-text-primary">{run.request_text}</p>
        <div className="mt-1 flex items-center gap-2 font-mono text-[10px] text-text-faint">
          <span>{run.requester}</span>
          <span>·</span>
          <span>{new Date(run.created_at).toLocaleString()}</span>
          {run.is_eval && (
            <>
              <span>·</span>
              <span className="text-signal-cyan">eval</span>
            </>
          )}
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-3">
        {run.confidence !== null && (
          <span className="font-mono text-[11px] tabular text-text-secondary">
            {(run.confidence * 100).toFixed(0)}%
          </span>
        )}
        {run.latency_ms !== null && (
          <span className="font-mono text-[11px] tabular text-text-faint">{run.latency_ms.toFixed(0)}ms</span>
        )}
        <StatusPill status={run.status} />
      </div>
    </Link>
  );
}
