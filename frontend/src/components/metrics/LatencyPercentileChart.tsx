import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { LatencyPercentiles } from "@/types";

export function LatencyPercentileChart({ latency }: { latency: LatencyPercentiles }) {
  const data = [
    { label: "p50", value: latency.p50 },
    { label: "p90", value: latency.p90 },
    { label: "p95", value: latency.p95 },
    { label: "p99", value: latency.p99 },
  ];

  return (
    <ResponsiveContainer width="100%" height={180}>
      <BarChart data={data} margin={{ top: 4, right: 8, left: -18, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1B222B" vertical={false} />
        <XAxis
          dataKey="label"
          tick={{ fill: "#8B98A5", fontSize: 11, fontFamily: "JetBrains Mono" }}
          axisLine={{ stroke: "#232C36" }}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: "#8B98A5", fontSize: 11, fontFamily: "JetBrains Mono" }}
          axisLine={false}
          tickLine={false}
          width={48}
          tickFormatter={(v) => `${v}ms`}
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
          labelStyle={{ color: "#8B98A5" }}
          formatter={(value: number) => [`${value.toFixed(1)}ms`, "latency"]}
        />
        <Bar dataKey="value" fill="#F0A83A" radius={[3, 3, 0, 0]} maxBarSize={44} />
      </BarChart>
    </ResponsiveContainer>
  );
}
