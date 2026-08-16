import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { CategoryStat } from "@/types";

const CATEGORY_LABELS: Record<string, string> = {
  missing_context: "Missing context",
  failed_tool_calls: "Failed tool calls",
  incorrect_retrieval: "Incorrect retrieval",
  unsafe_outputs: "Unsafe outputs",
  latency_issues: "Latency issues",
  approval_routing: "Approval routing",
  fallback_behavior: "Fallback behavior",
};

export function CategoryBreakdownChart({ data }: { data: CategoryStat[] }) {
  const chartData = data.map((d) => ({
    ...d,
    label: CATEGORY_LABELS[d.category] ?? d.category,
    pass_pct: Math.round(d.pass_rate * 100),
  }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart
        data={chartData}
        layout="vertical"
        margin={{ top: 4, right: 24, left: 8, bottom: 0 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#1B222B" horizontal={false} />
        <XAxis
          type="number"
          domain={[0, 100]}
          tick={{ fill: "#8B98A5", fontSize: 11, fontFamily: "JetBrains Mono" }}
          axisLine={{ stroke: "#232C36" }}
          tickLine={false}
          tickFormatter={(v) => `${v}%`}
        />
        <YAxis
          type="category"
          dataKey="label"
          tick={{ fill: "#E7ECF2", fontSize: 12, fontFamily: "Inter" }}
          axisLine={false}
          tickLine={false}
          width={140}
        />
        <Tooltip
          cursor={{ fill: "rgba(240,168,58,0.06)" }}
          contentStyle={{
            background: "#182029",
            border: "1px solid #232C36",
            borderRadius: 6,
            fontFamily: "JetBrains Mono",
            fontSize: 12,
          }}
          formatter={(value: number, _name, entry) => [
            `${entry.payload.passed}/${entry.payload.total} passed (${value}%)`,
            "pass rate",
          ]}
        />
        <Bar dataKey="pass_pct" radius={[0, 3, 3, 0]} maxBarSize={18}>
          {chartData.map((entry) => (
            <Cell key={entry.category} fill={entry.pass_pct === 100 ? "#3ABE8E" : "#F0A83A"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
