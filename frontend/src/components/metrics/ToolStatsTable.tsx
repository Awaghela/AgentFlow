import type { ToolStat } from "@/types";

export function ToolStatsTable({ tools }: { tools: ToolStat[] }) {
  if (tools.length === 0) {
    return <p className="font-mono text-xs text-text-faint">No tool calls recorded yet.</p>;
  }

  return (
    <table className="w-full border-collapse">
      <thead>
        <tr className="border-b border-border text-left">
          <th className="pb-2 font-mono text-[10px] uppercase tracking-wide text-text-faint">Tool</th>
          <th className="pb-2 font-mono text-[10px] uppercase tracking-wide text-text-faint text-right">Calls</th>
          <th className="pb-2 font-mono text-[10px] uppercase tracking-wide text-text-faint text-right">
            Success
          </th>
          <th className="pb-2 font-mono text-[10px] uppercase tracking-wide text-text-faint text-right">
            Avg latency
          </th>
        </tr>
      </thead>
      <tbody>
        {tools.map((t) => (
          <tr key={t.tool_name} className="border-b border-border-soft last:border-0">
            <td className="py-2 font-mono text-xs text-text-primary">{t.tool_name}</td>
            <td className="py-2 text-right font-mono text-xs tabular text-text-secondary">{t.calls}</td>
            <td
              className="py-2 text-right font-mono text-xs tabular"
              style={{ color: t.success_rate >= 0.9 ? "#3ABE8E" : t.success_rate >= 0.6 ? "#F0A83A" : "#E15554" }}
            >
              {Math.round(t.success_rate * 100)}%
            </td>
            <td className="py-2 text-right font-mono text-xs tabular text-text-secondary">
              {t.avg_latency_ms.toFixed(0)}ms
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
