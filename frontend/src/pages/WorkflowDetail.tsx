import { useParams, Link } from "react-router-dom";
import type { ReactNode } from "react";
import { ArrowLeft, CheckCircle2, ShieldAlert } from "lucide-react";
import clsx from "clsx";
import { api } from "@/api/client";
import { useAsync } from "@/hooks/useAsync";
import { TopBar } from "@/components/layout/TopBar";
import { Panel } from "@/components/common/Panel";
import { Loading, ErrorState } from "@/components/common/Loading";
import { StatusPill } from "@/components/common/StatusPill";
import { TraceTimeline } from "@/components/trace/TraceTimeline";
import { PlanList } from "@/components/trace/PlanList";
import type { WorkflowRunDetail } from "@/types";

export function WorkflowDetail() {
  const { id } = useParams<{ id: string }>();
  const { data: run, loading, error, refetch } = useAsync(() => api.getWorkflow(id!), [id]);

  if (loading) return <Page><Loading label="Loading result" /></Page>;
  if (error || !run)
    return (
      <Page>
        <ErrorState message={error ?? "not found"} onRetry={refetch} />
      </Page>
    );

  return (
    <Page>
      {/* The result is the answer to "what did the agent decide" — it's the
          thing a business user actually came here for, so it leads the page
          as a full-width hero rather than being buried under the trace. */}
      <ResultHero run={run} />

      <div className="mt-5 grid grid-cols-1 gap-5 lg:grid-cols-3">
        <div className="flex flex-col gap-5 lg:col-span-2">
          <Panel eyebrow="Audit trail" title="Execution timeline">
            <TraceTimeline steps={run.steps} />
          </Panel>
        </div>

        <div className="flex flex-col gap-5">
          <Panel eyebrow="Request" title="Summary">
            <p className="text-sm text-text-primary">{run.request_text}</p>
            <dl className="mt-4 flex flex-col gap-2 font-mono text-[11px]">
              <Row label="Requester">{run.requester}</Row>
              <Row label="Total latency">{run.latency_ms?.toFixed(1) ?? "—"}ms</Row>
              <Row label="Fallback count">{run.fallback_count}</Row>
              <Row label="Submitted">{new Date(run.created_at).toLocaleString()}</Row>
              {run.is_eval && <Row label="Source"><span className="text-signal-cyan">eval harness</span></Row>}
            </dl>
          </Panel>

          {run.plan && (
            <Panel eyebrow="Orchestration" title="Generated plan">
              <PlanList plan={run.plan} />
            </Panel>
          )}

          {run.approval && (
            <Panel eyebrow="Governance" title="Approval">
              <div className="flex flex-col gap-2 font-mono text-[11px]">
                <Row label="Status">
                  <StatusPill status={run.approval.status} />
                </Row>
                <Row label="Risk level">{run.approval.risk_level}</Row>
                <Row label="Reason"><span className="text-right text-text-secondary">{run.approval.reason}</span></Row>
                {run.approval.reviewer && <Row label="Reviewer">{run.approval.reviewer}</Row>}
                {run.approval.decision_notes && (
                  <Row label="Notes"><span className="text-right text-text-secondary">{run.approval.decision_notes}</span></Row>
                )}
              </div>
            </Panel>
          )}
        </div>
      </div>
    </Page>
  );
}

const HERO_BORDER_TONE: Record<string, string> = {
  completed: "border-signal-green/40",
  approved: "border-signal-green/40",
  auto_approved: "border-signal-green/40",
  pending_approval: "border-signal-amber/40",
  fallback: "border-signal-amber/40",
  rejected: "border-signal-red/40",
  failed: "border-signal-red/40",
};

function ResultHero({ run }: { run: WorkflowRunDetail }) {
  const borderTone = HERO_BORDER_TONE[run.status] ?? "border-border";
  const awaitingApproval = run.approval?.status === "pending";

  return (
    <div className={clsx("rounded-md border-2 bg-surface p-6 shadow-panel", borderTone)}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-text-faint">Result</p>
        <div className="flex items-center gap-3">
          {run.confidence !== null && (
            <span className="font-mono text-xs text-text-secondary">
              confidence <span className="text-text-primary tabular">{(run.confidence * 100).toFixed(0)}%</span>
            </span>
          )}
          <StatusPill status={run.status} />
        </div>
      </div>

      <p className="mt-4 font-display text-lg leading-relaxed text-text-primary">
        {run.final_output || "No output was generated for this run."}
      </p>

      {awaitingApproval && run.approval && (
        <div className="mt-4 flex items-start gap-2 rounded-sm border border-signal-amber/30 bg-signal-amberSoft px-3 py-2.5">
          <ShieldAlert size={14} className="mt-0.5 shrink-0 text-signal-amber" />
          <p className="font-mono text-[11px] text-signal-amber">
            Awaiting human approval — {run.approval.reason}
          </p>
        </div>
      )}

      {!awaitingApproval && run.approval?.status === "auto_approved" && (
        <div className="mt-4 flex items-center gap-2 font-mono text-[11px] text-signal-green">
          <CheckCircle2 size={13} />
          Auto-approved — confidence and risk were within threshold
        </div>
      )}
    </div>
  );
}

function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4">
      <dt className="text-text-faint">{label}</dt>
      <dd className="text-text-primary">{children}</dd>
    </div>
  );
}

function Page({ children }: { children: ReactNode }) {
  return (
    <>
      <TopBar
        title="Workflow result"
        description="The agent's recommendation, with the full auditable trace behind it."
        action={
          <Link to="/workflows" className="flex items-center gap-1.5 font-mono text-xs text-text-secondary hover:text-text-primary">
            <ArrowLeft size={14} /> Back to runs
          </Link>
        }
      />
      <div className="px-8 py-6">{children}</div>
    </>
  );
}
