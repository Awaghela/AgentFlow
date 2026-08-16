import type { PlanStep } from "@/types";

export function PlanList({ plan }: { plan: PlanStep[] }) {
  return (
    <ol className="flex flex-col gap-2">
      {plan.map((step) => (
        <li key={step.step} className="flex items-start gap-3">
          <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-sm border border-border bg-surface-raised font-mono text-[10px] text-text-secondary">
            {step.step}
          </span>
          <div>
            <p className="text-xs text-text-primary">{step.description}</p>
            {step.tool && (
              <span className="mt-0.5 inline-block rounded-sm border border-border bg-ink-950 px-1.5 py-0.5 font-mono text-[10px] text-signal-cyan">
                {step.tool}
              </span>
            )}
          </div>
        </li>
      ))}
    </ol>
  );
}
