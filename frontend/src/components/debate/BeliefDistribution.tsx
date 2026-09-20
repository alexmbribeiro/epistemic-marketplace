"use client";

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import type { BeliefDistribution } from "@/types";

/**
 * Belief runs false -> true, so this is a DIVERGING scale, not a categorical
 * one: two hues meeting at a neutral grey, lightness rising toward the middle.
 * It was a rainbow (rose/orange/amber/emerald/cyan), which reads as five
 * unrelated categories and hides that the axis is ordered.
 * Poles are the red and blue of the series palette so the two agree.
 */
const BUCKET_COLORS = ["#e66767", "#b47a86", "#6f7681", "#4a7cbd", "#3987e5"];

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

  const meanPct = Math.round(distribution.mean * 100);
  const meanLabel =
    distribution.mean > 0.65
      ? "Likely True"
      : distribution.mean < 0.35
      ? "Likely False"
      : "Uncertain";
  // Same diverging logic as the bars: the headline must not say "cyan = true"
  // while the chart says something else.
  const meanColor =
    distribution.mean > 0.65
      ? "text-[#6ea8ea]"
      : distribution.mean < 0.35
      ? "text-[#e88b8b]"
      : "text-white/70";

  return (
    <div className="space-y-4">
      <div className="flex items-baseline gap-3">
        <span className={`display text-[40px] tabular-nums ${meanColor}`}>{meanPct}%</span>
        <span className={`text-lg font-semibold ${meanColor}`}>{meanLabel}</span>
        <span className="text-white/35 text-sm ml-auto">±{Math.round(distribution.std * 100)}% std</span>
      </div>

      <ResponsiveContainer width="100%" height={120}>
        <BarChart data={data} barCategoryGap="20%">
          <XAxis dataKey="range" tick={{ fontSize: 10, fill: "rgba(255,255,255,0.38)" }} />
          <YAxis hide />
          <Tooltip
            contentStyle={{ background: "rgba(18,20,26,0.92)", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 14, backdropFilter: "blur(20px)" }}
            labelStyle={{ color: "rgba(255,255,255,0.55)" }}
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
        <p className="text-xs text-white/40">Zone of disagreement</p>
        <p className="text-sm text-amber-300/80 italic">"{distribution.disagreement_zone}"</p>
      </div>

      {distribution.dominant_agents.length > 0 && (
        <div className="space-y-1">
          <p className="text-xs text-white/40">Most influential</p>
          <div className="flex flex-wrap gap-2">
            {distribution.dominant_agents.map((a, i) => (
              <span key={i} className="text-xs bg-white/[0.07] border border-white/15 px-2 py-1 rounded-full text-white/75">
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
