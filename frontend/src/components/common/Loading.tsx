export function Loading({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 py-12 text-text-secondary">
      <span className="relative flex h-3 w-3">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-signal-amber opacity-60" />
        <span className="relative inline-flex h-3 w-3 rounded-full bg-signal-amber" />
      </span>
      <span className="font-mono text-xs uppercase tracking-wide">{label}…</span>
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-start gap-3 rounded border border-signal-red/30 bg-signal-redSoft/40 px-4 py-4">
      <p className="font-mono text-xs text-signal-red">Couldn't load this — {message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="rounded-sm border border-signal-red/40 px-3 py-1 font-mono text-[11px] uppercase text-signal-red hover:bg-signal-red/10"
        >
          Retry
        </button>
      )}
    </div>
  );
}

export function EmptyState({ title, description }: { title: string; description?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-1 rounded border border-dashed border-border py-14 text-center">
      <p className="font-display text-sm text-text-secondary">{title}</p>
      {description && <p className="max-w-sm text-xs text-text-faint">{description}</p>}
    </div>
  );
}
