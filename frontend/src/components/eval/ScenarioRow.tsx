import { useState } from "react";
import clsx from "clsx";
import { CheckCircle2, XCircle, ChevronDown } from "lucide-react";
import type { EvalResult, EvalScenario } from "@/types";

export function ScenarioRow({ scenario, result }: { scenario: EvalScenario; result?: EvalResult }) {
  const [open, setOpen] = useState(false);
  const passed = result?.passed ?? null;

  return (
    <div className="border-b border-border-soft last:border-0">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-3 py-2.5 text-left transition-colors hover:bg-surface-hover"
      >
        {passed === null ? (
          <span className="h-3.5 w-3.5 shrink-0 rounded-full border border-text-faint" />
        ) : passed ? (
          <CheckCircle2 size={14} className="shrink-0 text-signal-green" />
        ) : (
          <XCircle size={14} className="shrink-0 text-signal-red" />
        )}
        <span className="flex-1 truncate font-mono text-xs text-text-primary">{scenario.name}</span>
        <span
          className={clsx(
            "rounded-sm border px-1.5 py-0.5 font-mono text-[9px] uppercase",
            scenario.severity === "critical"
              ? "border-signal-red/30 text-signal-red"
              : scenario.severity === "high"
              ? "border-signal-amber/30 text-signal-amber"
              : "border-border text-text-faint"
          )}
        >
          {scenario.severity}
        </span>
        {result && <span className="font-mono text-[10px] tabular text-text-faint">{result.latency_ms.toFixed(0)}ms</span>}
        <ChevronDown size={13} className={clsx("text-text-faint transition-transform", open && "rotate-180")} />
      </button>

      {open && (
        <div className="mb-2 rounded border border-border bg-ink-950/60 p-3 text-xs">
          <p className="text-text-secondary">{scenario.description}</p>
          <p className="mt-1.5 font-mono text-[10px] uppercase tracking-wide text-text-faint">Expected behavior</p>
          <p className="mt-0.5 text-text-secondary">{scenario.expected_behavior}</p>

          {result && (
            <>
              <p className="mt-2.5 font-mono text-[10px] uppercase tracking-wide text-text-faint">Assertions</p>
              <ul className="mt-1 flex flex-col gap-0.5">
                {result.assertions.map((a, i) => (
                  <li
                    key={i}
                    className={clsx(
                      "font-mono text-[10px]",
                      a.startsWith("PASS") ? "text-signal-green" : "text-signal-red"
                    )}
                  >
                    {a}
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}
    </div>
  );
}
