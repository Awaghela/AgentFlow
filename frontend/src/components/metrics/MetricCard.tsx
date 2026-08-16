import type { ReactNode } from "react";
import clsx from "clsx";

export function MetricCard({
  label,
  value,
  suffix,
  trend,
  tone = "neutral",
  icon,
}: {
  label: string;
  value: string;
  suffix?: string;
  trend?: string;
  tone?: "neutral" | "green" | "amber" | "red";
  icon?: ReactNode;
}) {
  const toneClass = {
    neutral: "text-text-primary",
    green: "text-signal-green",
    amber: "text-signal-amber",
    red: "text-signal-red",
  }[tone];

  return (
    <div className="rounded-md border border-border bg-surface p-4 shadow-panel">
      <div className="flex items-center justify-between">
        <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-text-faint">{label}</p>
        {icon && <span className="text-text-faint">{icon}</span>}
      </div>
      <div className="mt-2 flex items-baseline gap-1.5">
        <span className={clsx("font-mono text-2xl font-medium tabular", toneClass)}>{value}</span>
        {suffix && <span className="font-mono text-xs text-text-faint">{suffix}</span>}
      </div>
      {trend && <p className="mt-1 font-mono text-[11px] text-text-secondary">{trend}</p>}
    </div>
  );
}
