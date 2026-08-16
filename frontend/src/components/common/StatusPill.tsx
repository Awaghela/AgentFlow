import clsx from "clsx";

type Tone = "green" | "amber" | "red" | "cyan" | "neutral";

const STATUS_TONE: Record<string, Tone> = {
  planning: "cyan",
  retrieving: "cyan",
  executing_tools: "cyan",
  validating: "cyan",
  pending_approval: "amber",
  fallback: "amber",
  approved: "green",
  completed: "green",
  auto_approved: "green",
  rejected: "red",
  failed: "red",
  pending: "amber",
};

const TONE_CLASSES: Record<Tone, { dot: string; text: string }> = {
  green: { dot: "bg-signal-green shadow-[0_0_6px_rgba(58,190,142,0.7)]", text: "text-signal-green" },
  amber: { dot: "bg-signal-amber shadow-[0_0_6px_rgba(240,168,58,0.7)]", text: "text-signal-amber" },
  red: { dot: "bg-signal-red shadow-[0_0_6px_rgba(225,85,84,0.7)]", text: "text-signal-red" },
  cyan: { dot: "bg-signal-cyan shadow-[0_0_6px_rgba(79,184,214,0.7)]", text: "text-signal-cyan" },
  neutral: { dot: "bg-text-faint", text: "text-text-secondary" },
};

function formatLabel(status: string): string {
  return status.replace(/_/g, " ");
}

export function StatusPill({ status, className }: { status: string; className?: string }) {
  const tone = STATUS_TONE[status] ?? "neutral";
  const cls = TONE_CLASSES[tone];

  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-sm border border-border bg-surface px-2 py-0.5 font-mono text-[11px] uppercase tracking-wide",
        cls.text,
        className
      )}
    >
      <span className={clsx("h-1.5 w-1.5 rounded-full", cls.dot)} />
      {formatLabel(status)}
    </span>
  );
}
