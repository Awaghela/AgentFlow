import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { StatusBreakdownEntry } from "@/types";

const COLORS: Record<string, string> = {
  completed: "#3ABE8E",
  pending_approval: "#F0A83A",
  fallback: "#F0A83A",
  planning: "#4FB8D6",
  retrieving: "#4FB8D6",
  executing_tools: "#4FB8D6",
  validating: "#4FB8D6",
  approved: "#3ABE8E",
  rejected: "#E15554",
  failed: "#E15554",
};

export function StatusDonut({ data }: { data: StatusBreakdownEntry[] }) {
  const total = data.reduce((sum, d) => sum + d.count, 0);

  return (
    <div className="flex items-center gap-6">
      <ResponsiveContainer width={140} height={140}>
        <PieChart>
          <Pie
            data={data}
            dataKey="count"
            nameKey="status"
            innerRadius={42}
            outerRadius={64}
            paddingAngle={2}
            stroke="none"
          >
            {data.map((entry) => (
              <Cell key={entry.status} fill={COLORS[entry.status] ?? "#5C6773"} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              background: "#182029",
              border: "1px solid #232C36",
              borderRadius: 6,
              fontFamily: "JetBrains Mono",
              fontSize: 12,
            }}
            formatter={(value: number, _name, entry) => [
              `${value} (${total ? Math.round((value / total) * 100) : 0}%)`,
              String(entry.payload.status).replace(/_/g, " "),
            ]}
          />
        </PieChart>
      </ResponsiveContainer>
      <ul className="flex flex-col gap-1.5">
        {data.map((d) => (
          <li key={d.status} className="flex items-center gap-2 font-mono text-[11px]">
            <span
              className="h-2 w-2 rounded-full"
              style={{ background: COLORS[d.status] ?? "#5C6773" }}
            />
            <span className="text-text-secondary">{d.status.replace(/_/g, " ")}</span>
            <span className="text-text-primary tabular">{d.count}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
