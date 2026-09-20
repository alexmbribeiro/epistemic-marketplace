"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Trajectory } from "@/types";
import { SURFACE, agentColor } from "@/lib/agentColors";

interface Props {
  trajectory: Trajectory;
}

const ROUND_PHASES = ["Independent", "Cross-challenge", "Synthesis"];

interface TipPayload {
  name: string;
  value: number;
  color: string;
}

function Tip({ active, payload, label }: { active?: boolean; payload?: TipPayload[]; label?: string }) {
  if (!active || !payload?.length) return null;
  const idx = Number(String(label).replace(/\D/g, "")) - 1;
  const phase = ROUND_PHASES[idx];
  const rows = [...payload].sort((a, b) => b.value - a.value);
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 shadow-xl">
      <p className="text-xs text-slate-400 mb-1.5">
        {label}
        {phase ? <span className="text-slate-500"> · {phase}</span> : null}
      </p>
      {rows.map((r) => (
        <div key={r.name} className="flex items-center gap-2 text-xs">
          <span className="w-2 h-2 rounded-full shrink-0" style={{ background: r.color }} />
          <span className="text-slate-300">{r.name}</span>
          <span className="ml-auto font-mono text-slate-100">{Math.round(r.value * 100)}%</span>
        </div>
      ))}
    </div>
  );
}

export default function BeliefTrajectory({ trajectory }: Props) {
  const { agents } = trajectory;
  if (!agents?.length) return null;

  const rounds = agents[0].beliefs.length;
  const data = Array.from({ length: rounds }, (_, i) => {
    // Short tick labels — the phase name goes in the tooltip, where there is
    // room for it. Spelled out on the axis, Recharts drops ticks to fit.
    const point: Record<string, string | number> = { round: `Round ${i + 1}` };
    agents.forEach((a) => {
      point[a.agent_name] = a.beliefs[i];
    });
    return point;
  });

  const spread = trajectory.spread_per_round ?? [];
  const convergence = trajectory.convergence;
  const convergenceCopy =
    convergence === "converged"
      ? "Agents moved closer together"
      : convergence === "diverged"
      ? "Agents moved further apart"
      : "Spread held roughly steady";

  return (
    <div className="space-y-4">
      <div className="flex items-baseline gap-2 flex-wrap">
        <span className="text-sm text-slate-300">{convergenceCopy}</span>
        {spread.length >= 2 && (
          <span className="text-xs text-slate-500 font-mono">
            spread {Math.round(spread[0] * 100)}% → {Math.round(spread[spread.length - 1] * 100)}%
          </span>
        )}
        {(trajectory.reversals?.length ?? 0) > 0 && (
          <span className="text-xs text-amber-300/80 ml-auto">
            changed direction mid-debate: {trajectory.reversals.join(", ")}
          </span>
        )}
      </div>

      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 4, left: -16 }}>
          <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="round"
            tick={{ fontSize: 11, fill: "#64748b" }}
            axisLine={{ stroke: "#1e293b" }}
            tickLine={false}
            interval={0}
          />
          <YAxis
            domain={[0, 1]}
            ticks={[0, 0.25, 0.5, 0.75, 1]}
            tickFormatter={(v: number) => `${Math.round(v * 100)}%`}
            tick={{ fontSize: 11, fill: "#64748b" }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip content={<Tip />} cursor={{ stroke: "#334155", strokeWidth: 1 }} />
          <Legend
            wrapperStyle={{ fontSize: 11, paddingTop: 8 }}
            iconType="plainline"
            formatter={(value: string) => <span className="text-slate-400">{value}</span>}
          />
          {agents.map((a) => (
            <Line
              key={a.agent_id}
              type="monotone"
              dataKey={a.agent_name}
              stroke={agentColor(a.archetype)}
              strokeWidth={2}
              // 2px surface ring keeps overlapping markers readable
              dot={{ r: 4, fill: agentColor(a.archetype), stroke: SURFACE, strokeWidth: 2 }}
              activeDot={{ r: 6, stroke: SURFACE, strokeWidth: 2 }}
              isAnimationActive={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>

      {/* Table view — also the "who moved" readout */}
      <table className="w-full text-xs">
        <thead>
          <tr className="text-slate-500 text-left">
            <th className="font-normal pb-1">Agent</th>
            {Array.from({ length: rounds }, (_, i) => (
              <th key={i} className="font-normal pb-1 text-right">R{i + 1}</th>
            ))}
            <th className="font-normal pb-1 text-right">Travelled</th>
          </tr>
        </thead>
        <tbody>
          {[...agents]
            .sort((a, b) => (b.swing ?? 0) - (a.swing ?? 0))
            .map((a) => (
              <tr key={a.agent_id} className="border-t border-slate-800/70">
                <td className="py-1.5">
                  <span className="flex items-center gap-2">
                    <span
                      className="w-2 h-2 rounded-full shrink-0"
                      style={{ background: agentColor(a.archetype) }}
                    />
                    <span className="text-slate-300">{a.agent_name}</span>
                    {a.reversed && (
                      <span className="text-[10px] text-amber-300/90 border border-amber-500/40 rounded px-1">
                        reversed
                      </span>
                    )}
                  </span>
                </td>
                {a.beliefs.map((b, i) => (
                  <td key={i} className="py-1.5 text-right font-mono text-slate-400">
                    {Math.round(b * 100)}%
                  </td>
                ))}
                <td className="py-1.5 text-right font-mono text-slate-300">
                  {a.swing == null
                    ? "—"
                    : a.swing === 0
                    ? "—"
                    : `${Math.round(a.swing * 100)}pp`}
                </td>
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  );
}
