"use client";

import { useQuery } from "@tanstack/react-query";
import { calibrationApi } from "@/lib/api";
import { paletteFor } from "@/lib/agentColors";

const CRITERIA = [
  ["method_fidelity", "Method"],
  ["engagement", "Engagement"],
  ["crux_quality", "Cruxes"],
  ["responsiveness", "Responsive"],
] as const;

export default function CalibrationPage() {
  const { data: board, isLoading } = useQuery({
    queryKey: ["calibration-leaderboard"],
    queryFn: () => calibrationApi.leaderboard(),
  });
  const { data: bias } = useQuery({
    queryKey: ["judge-bias"],
    queryFn: () => calibrationApi.judgeBias(),
  });

  const palette = paletteFor((board ?? []).map((a) => a.archetype));

  // How severe each judge is overall. Within one debate this mostly cancels —
  // every participant faced the same panel — but it is worth seeing.
  const severity = new Map<string, { total: number; n: number }>();
  for (const row of bias ?? []) {
    const cur = severity.get(row.judge) ?? { total: 0, n: 0 };
    severity.set(row.judge, { total: cur.total + row.mean_score * row.n, n: cur.n + row.n });
  }
  const judges = Array.from(severity.entries())
    .map(([judge, s]) => ({ judge, mean: s.total / s.n }))
    .sort((a, b) => a.mean - b.mean);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Ranking</h1>
        <p className="text-slate-500 text-sm mt-1 max-w-2xl">
          After each debate, three philosophers who took no part read the transcript and score
          every participant on craft — not on whether they agree. Those scores become pairwise
          results and move an Elo, starting from 1500.
        </p>
      </div>

      {isLoading && <div className="text-slate-500 text-sm">Loading…</div>}

      <div className="rounded-xl border border-slate-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-900/80 text-slate-500">
              <th className="text-left px-4 py-3 font-medium">#</th>
              <th className="text-left px-4 py-3 font-medium">Agent</th>
              <th className="text-right px-4 py-3 font-medium">Elo</th>
              <th className="text-right px-4 py-3 font-medium">Debated</th>
              <th className="text-right px-4 py-3 font-medium">Judged</th>
              {CRITERIA.map(([, label]) => (
                <th key={label} className="text-right px-3 py-3 font-medium hidden md:table-cell">
                  {label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {board?.map((a, i) => (
              <tr key={a.agent_id} className="border-b border-slate-800/50 hover:bg-slate-900/30">
                <td className="px-4 py-3 text-slate-600 font-mono">{i + 1}</td>
                <td className="px-4 py-3">
                  <span className="flex items-center gap-2">
                    <span
                      className="w-2 h-2 rounded-full shrink-0"
                      style={{ background: palette[a.archetype] }}
                    />
                    <span className="font-medium text-slate-200">{a.name}</span>
                    {a.provisional && (
                      <span
                        className="text-[10px] text-slate-500 border border-slate-700 rounded px-1"
                        title="Fewer than five rated debates — this number is mostly noise"
                      >
                        provisional
                      </span>
                    )}
                  </span>
                </td>
                <td className="px-4 py-3 text-right font-mono font-bold text-slate-100">
                  {a.elo_rating.toFixed(0)}
                  <span
                    className={`ml-2 text-xs font-normal ${
                      a.elo_rating > 1500 ? "text-emerald-400" : a.elo_rating < 1500 ? "text-rose-400" : "text-slate-600"
                    }`}
                  >
                    {a.elo_rating === 1500 ? "—" : `${a.elo_rating > 1500 ? "+" : ""}${(a.elo_rating - 1500).toFixed(0)}`}
                  </span>
                </td>
                <td className="px-4 py-3 text-right font-mono text-slate-400">{a.debates_rated_in}</td>
                <td className="px-4 py-3 text-right font-mono text-slate-400">{a.debates_judged}</td>
                {CRITERIA.map(([key]) => (
                  <td key={key} className="px-3 py-3 text-right font-mono text-slate-500 hidden md:table-cell">
                    {a.criteria ? a.criteria[key].toFixed(0) : "—"}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {judges.length > 0 && (
        <div className="space-y-2">
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Judge severity</h2>
          <p className="text-xs text-slate-600 max-w-2xl">
            The mean score each philosopher hands out. A philosopher judging philosophers brings
            its school with it, and this is where that shows. Within a single debate it largely
            cancels — everyone faced the same panel — but a judge that is harsh on one school
            specifically does not cancel, and that is the limit of the ranking.
          </p>
          <div className="flex flex-wrap gap-2 pt-1">
            {judges.map((j) => (
              <span
                key={j.judge}
                className="text-xs border border-slate-800 bg-slate-900/50 rounded-full px-3 py-1.5 text-slate-400"
              >
                {j.judge} <span className="font-mono text-slate-300">{j.mean.toFixed(0)}</span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
