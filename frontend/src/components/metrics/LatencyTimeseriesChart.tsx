import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { LatencyTimeseriesPoint } from "@/types";

export function LatencyTimeseriesChart({ points }: { points: LatencyTimeseriesPoint[] }) {
  if (points.length === 0) {
    return (
      <div className="flex h-[180px] items-center justify-center font-mono text-xs text-text-faint">
        no timeseries data yet
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={180}>
      <LineChart data={points} margin={{ top: 4, right: 8, left: -18, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1B222B" vertical={false} />
        <XAxis
          dataKey="bucket"
          tick={{ fill: "#8B98A5", fontSize: 10, fontFamily: "JetBrains Mono" }}
          axisLine={{ stroke: "#232C36" }}
          tickLine={false}
          minTickGap={40}
        />
        <YAxis
          tick={{ fill: "#8B98A5", fontSize: 11, fontFamily: "JetBrains Mono" }}
          axisLine={false}
          tickLine={false}
          width={48}
          tickFormatter={(v) => `${v}ms`}
        />
        <Tooltip
          contentStyle={{
            background: "#182029",
            border: "1px solid #232C36",
            borderRadius: 6,
            fontFamily: "JetBrains Mono",
            fontSize: 12,
          }}
          labelStyle={{ color: "#8B98A5" }}
          formatter={(value: number) => [`${value.toFixed(1)}ms`, "avg latency"]}
        />
        <Line
          type="monotone"
          dataKey="avg_latency_ms"
          stroke="#4FB8D6"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4, fill: "#4FB8D6" }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
