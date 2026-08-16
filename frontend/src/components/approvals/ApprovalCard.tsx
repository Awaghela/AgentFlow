import { useState } from "react";
import { Link } from "react-router-dom";
import { CheckCircle2, XCircle } from "lucide-react";
import type { Approval } from "@/types";
import { StatusPill } from "@/components/common/StatusPill";

const RISK_TONE: Record<string, string> = {
  low: "text-signal-green border-signal-green/30",
  medium: "text-signal-amber border-signal-amber/30",
  high: "text-signal-red border-signal-red/30",
};

export function ApprovalCard({
  approval,
  onDecide,
}: {
  approval: Approval;
  onDecide: (decision: "approved" | "rejected", notes?: string) => Promise<void>;
}) {
  const [busy, setBusy] = useState<"approved" | "rejected" | null>(null);
  const [notes, setNotes] = useState("");
  const run = approval.workflow_run;

  async function handle(decision: "approved" | "rejected") {
    setBusy(decision);
    try {
      await onDecide(decision, notes || undefined);
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="rounded-md border border-border bg-surface p-4 shadow-panel">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <Link
            to={`/workflows/${run.id}`}
            className="font-display text-sm text-text-primary hover:text-signal-amber"
          >
            {run.request_text}
          </Link>
          <p className="mt-1 line-clamp-2 font-mono text-[11px] text-text-secondary">{approval.reason}</p>
        </div>
        <span
          className={`shrink-0 rounded-sm border px-2 py-0.5 font-mono text-[10px] uppercase ${RISK_TONE[approval.risk_level]}`}
        >
          {approval.risk_level} risk
        </span>
      </div>

      <div className="mt-3 flex items-center gap-3 font-mono text-[11px] text-text-faint">
        <span>confidence {(approval.confidence_at_request * 100).toFixed(0)}%</span>
        <span>·</span>
        <span>requested by {run.requester}</span>
        <span>·</span>
        <StatusPill status={run.status} />
      </div>

      <textarea
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        placeholder="Optional review notes…"
        rows={2}
        className="mt-3 w-full resize-none rounded-sm border border-border bg-ink-950 px-2.5 py-2 font-mono text-[11px] text-text-primary placeholder:text-text-faint focus:border-signal-amber/50"
      />

      <div className="mt-3 flex gap-2">
        <button
          onClick={() => handle("approved")}
          disabled={busy !== null}
          className="flex flex-1 items-center justify-center gap-1.5 rounded-sm border border-signal-green/40 bg-signal-greenSoft px-3 py-1.5 font-mono text-[11px] uppercase tracking-wide text-signal-green transition-opacity hover:opacity-80 disabled:opacity-40"
        >
          <CheckCircle2 size={13} />
          {busy === "approved" ? "Approving…" : "Approve"}
        </button>
        <button
          onClick={() => handle("rejected")}
          disabled={busy !== null}
          className="flex flex-1 items-center justify-center gap-1.5 rounded-sm border border-signal-red/40 bg-signal-redSoft px-3 py-1.5 font-mono text-[11px] uppercase tracking-wide text-signal-red transition-opacity hover:opacity-80 disabled:opacity-40"
        >
          <XCircle size={13} />
          {busy === "rejected" ? "Rejecting…" : "Reject"}
        </button>
      </div>
    </div>
  );
}
