import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Loader2 } from "lucide-react";
import { api } from "@/api/client";

const EXAMPLES = [
  "What's the pricing for the Growth plan?",
  "Look up account acct_enterprise and summarize their plan and ARR.",
  "Calculate a refund for a $299 plan with 5 days used this period.",
  "Draft a response about a security incident for account acct_growth.",
];

export function NewRequestForm() {
  const [value, setValue] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  async function submit() {
    if (!value.trim() || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const run = await api.createWorkflow(value.trim());
      navigate(`/workflows/${run.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit request");
      setSubmitting(false);
    }
  }

  return (
    <div>
      <div className="flex gap-2">
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
          placeholder="Describe a business request for the agent to plan and execute…"
          className="flex-1 rounded-sm border border-border bg-ink-950 px-3 py-2.5 text-sm text-text-primary placeholder:text-text-faint focus:border-signal-amber/50"
        />
        <button
          onClick={submit}
          disabled={submitting || !value.trim()}
          className="flex items-center gap-2 rounded-sm border border-signal-amber/40 bg-signal-amberSoft px-4 py-2.5 font-mono text-xs uppercase tracking-wide text-signal-amber transition-opacity hover:opacity-80 disabled:opacity-40"
        >
          {submitting ? <Loader2 size={14} className="animate-spin" /> : <ArrowRight size={14} />}
          Run
        </button>
      </div>
      {error && <p className="mt-2 font-mono text-xs text-signal-red">{error}</p>}
      <div className="mt-3 flex flex-wrap gap-1.5">
        {EXAMPLES.map((ex) => (
          <button
            key={ex}
            onClick={() => setValue(ex)}
            className="rounded-sm border border-border px-2 py-1 font-mono text-[10px] text-text-faint transition-colors hover:border-signal-amber/30 hover:text-signal-amber"
          >
            {ex}
          </button>
        ))}
      </div>
    </div>
  );
}
