"use client";

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import type { BeliefDistribution } from "@/types";

const BUCKET_COLORS = ["#f43f5e", "#fb923c", "#f59e0b", "#34d399", "#22d3ee"];

interface Props {
  distribution: BeliefDistribution;
}

export default function BeliefDistributionChart({ distribution }: Props) {
  const data = distribution.buckets.map((b, i) => ({
    range: b.range,
    count: b.count,
    pct: Math.round(b.pct * 100),
    color: BUCKET_COLORS[i],
  }));

  const meanPct = Math.round(distribution.weighted_mean * 100);
  const meanLabel =
    distribution.weighted_mean > 0.65
      ? "Likely True"
      : distribution.weighted_mean < 0.35
      ? "Likely False"
      : "Uncertain";
  const meanColor =
    distribution.weighted_mean > 0.65
      ? "text-cyan-400"
      : distribution.weighted_mean < 0.35
      ? "text-rose-400"
      : "text-amber-400";

  return (
    <div className="space-y-4">
      <div className="flex items-baseline gap-3">
        <span className={`text-4xl font-bold font-mono ${meanColor}`}>{meanPct}%</span>
        <span className={`text-lg font-semibold ${meanColor}`}>{meanLabel}</span>
        <span className="text-slate-500 text-sm ml-auto">±{Math.round(distribution.std * 100)}% std</span>
      </div>

      <ResponsiveContainer width="100%" height={120}>
        <BarChart data={data} barCategoryGap="20%">
          <XAxis dataKey="range" tick={{ fontSize: 10, fill: "#64748b" }} />
          <YAxis hide />
          <Tooltip
            contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
            labelStyle={{ color: "#94a3b8" }}
            formatter={(v: number) => [`${v} agent${v !== 1 ? "s" : ""}`, "Count"]}
          />
          <Bar dataKey="count" radius={[4, 4, 0, 0]}>
            {data.map((entry, i) => (
              <Cell key={i} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div className="space-y-1">
        <p className="text-xs text-slate-500">Zone of disagreement</p>
        <p className="text-sm text-amber-300/80 italic">"{distribution.disagreement_zone}"</p>
      </div>

      {distribution.dominant_agents.length > 0 && (
        <div className="space-y-1">
          <p className="text-xs text-slate-500">Most influential</p>
          <div className="flex flex-wrap gap-2">
            {distribution.dominant_agents.map((a, i) => (
              <span key={i} className="text-xs bg-slate-800 border border-slate-700 px-2 py-1 rounded-full text-slate-300">
                {a.agent_name}{" "}
                <span className={a.belief_score > 0.5 ? "text-cyan-400" : "text-rose-400"}>
                  {Math.round(a.belief_score * 100)}%
                </span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
