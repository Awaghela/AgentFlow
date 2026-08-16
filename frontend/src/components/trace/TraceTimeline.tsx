import { useState } from "react";
import type { ReactNode } from "react";
import clsx from "clsx";
import type { AgentStep } from "@/types";
import { StatusPill } from "@/components/common/StatusPill";

const NODE_LABELS: Record<string, string> = {
  plan: "Plan",
  retrieve: "Retrieve context",
  tool_call: "Tool execution",
  fallback: "Fallback",
  validate: "Validate",
  respond: "Synthesize response",
  approval: "Approval gate",
};

const NODE_TONE: Record<string, string> = {
  success: "bg-signal-green",
  empty: "bg-signal-amber",
  flagged: "bg-signal-amber",
  degraded: "bg-signal-amber",
  failed: "bg-signal-red",
  pending_approval: "bg-signal-amber",
  auto_approved: "bg-signal-green",
};

export function TraceTimeline({ steps }: { steps: AgentStep[] }) {
  const maxLatency = Math.max(1, ...steps.map((s) => s.latency_ms));

  return (
    <div className="relative">
      {/* the vertical spine — the "flight recorder tape" */}
      <div className="absolute bottom-2 left-[15px] top-2 w-px bg-border" aria-hidden />

      <ol className="flex flex-col gap-1">
        {steps.map((step, i) => (
          <TraceStepRow
            key={step.id}
            step={step}
            index={i}
            maxLatency={maxLatency}
            isLast={i === steps.length - 1}
          />
        ))}
      </ol>
    </div>
  );
}

function TraceStepRow({
  step,
  index,
  maxLatency,
}: {
  step: AgentStep;
  index: number;
  maxLatency: number;
  isLast: boolean;
}) {
  const [open, setOpen] = useState(false);
  const tone = NODE_TONE[step.status] ?? "bg-signal-cyan";
  const widthPct = Math.max(4, Math.min(100, (step.latency_ms / maxLatency) * 100));

  return (
    <li className="relative pl-10">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="group flex w-full items-start gap-3 rounded-sm py-2.5 text-left transition-colors hover:bg-surface-hover"
      >
        <span
          className={clsx(
            "absolute left-[10px] top-3.5 h-3 w-3 -translate-x-1/2 rounded-full border-2 border-ink-950",
            tone
          )}
        />

        <div className="flex-1">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <span className="font-mono text-[10px] text-text-faint">{String(index + 1).padStart(2, "0")}</span>
              <span className="font-display text-sm text-text-primary">
                {NODE_LABELS[step.node_name] ?? step.node_name}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-[11px] tabular text-text-secondary">
                {step.latency_ms.toFixed(1)}ms
              </span>
              <StatusPill status={step.status} />
            </div>
          </div>

          {/* the oscilloscope-style latency tick */}
          <div className="mt-1.5 h-[3px] w-full overflow-hidden rounded-full bg-border-soft">
            <div
              className={clsx("h-full rounded-full", tone)}
              style={{ width: `${widthPct}%` }}
            />
          </div>

          {step.error && (
            <p className="mt-1.5 font-mono text-[11px] text-signal-red">{step.error}</p>
          )}
        </div>
      </button>

      {open && <StepDetail step={step} />}
    </li>
  );
}

function StepDetail({ step }: { step: AgentStep }) {
  return (
    <div className="mb-2 ml-10 rounded border border-border bg-ink-950/60 p-3.5 text-xs">
      {step.output_data && (
        <DetailBlock label="Output">
          <pre className="whitespace-pre-wrap break-words font-mono text-[11px] text-text-secondary">
            {JSON.stringify(step.output_data, null, 2)}
          </pre>
        </DetailBlock>
      )}

      {step.retrieval && (
        <DetailBlock label={`Retrieval — ${step.retrieval.num_results} doc(s)`}>
          <div className="flex flex-wrap items-center gap-2">
            <p className="font-mono text-[11px] text-text-secondary">
              top score {step.retrieval.top_score.toFixed(3)} · avg score {step.retrieval.avg_score.toFixed(3)}
              {step.retrieval.candidates_considered > step.retrieval.num_results && (
                <> · {step.retrieval.candidates_considered} candidates considered</>
              )}
            </p>
            {step.retrieval.reranked ? (
              <span className="rounded-sm border border-signal-green/30 bg-signal-greenSoft px-1.5 py-0.5 font-mono text-[10px] uppercase text-signal-green">
                ✓ reranked via cohere
              </span>
            ) : (
              step.retrieval.candidates_considered > step.retrieval.num_results && (
                <span
                  className="rounded-sm border border-signal-amber/30 bg-signal-amberSoft px-1.5 py-0.5 font-mono text-[10px] uppercase text-signal-amber"
                  title="A wider candidate pool was fetched (implying reranking was configured) but the rerank call didn't succeed — check backend logs for the reason."
                >
                  rerank not applied
                </span>
              )
            )}
          </div>
          {step.retrieval.retrieved_doc_ids.length > 0 && (
            <div className="mt-1 flex flex-wrap gap-1">
              {step.retrieval.retrieved_doc_ids.map((id) => (
                <span
                  key={id}
                  className="rounded-sm border border-border bg-surface-raised px-1.5 py-0.5 font-mono text-[10px] text-signal-cyan"
                >
                  {id}
                </span>
              ))}
            </div>
          )}
        </DetailBlock>
      )}

      {step.tool_calls.length > 0 && (
        <DetailBlock label="Tool calls">
          <div className="flex flex-col gap-2">
            {step.tool_calls.map((tc) => (
              <div
                key={tc.id}
                className={clsx(
                  "rounded-sm border px-2.5 py-2",
                  tc.success ? "border-border bg-surface-raised" : "border-signal-red/30 bg-signal-redSoft/30"
                )}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[11px] text-text-primary">{tc.tool_name}</span>
                  <span className={clsx("font-mono text-[10px]", tc.success ? "text-signal-green" : "text-signal-red")}>
                    {tc.success ? "ok" : "failed"} · {tc.latency_ms.toFixed(0)}ms
                  </span>
                </div>
                {tc.arguments && (
                  <p className="mt-1 truncate font-mono text-[10px] text-text-faint">
                    args: {JSON.stringify(tc.arguments)}
                  </p>
                )}
                {tc.error && <p className="mt-1 font-mono text-[10px] text-signal-red">{tc.error}</p>}
              </div>
            ))}
          </div>
        </DetailBlock>
      )}
    </div>
  );
}

function DetailBlock({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="mb-3 last:mb-0">
      <p className="mb-1 font-mono text-[10px] uppercase tracking-wide text-text-faint">{label}</p>
      {children}
    </div>
  );
}
