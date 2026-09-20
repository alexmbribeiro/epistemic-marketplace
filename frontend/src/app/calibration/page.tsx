"use client";

import { useQuery } from "@tanstack/react-query";
import { calibrationApi } from "@/lib/api";

export default function CalibrationPage() {
  const { data: leaderboard, isLoading } = useQuery({
    queryKey: ["calibration-leaderboard"],
    queryFn: () => calibrationApi.leaderboard(),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Calibration Leaderboard</h1>
        <p className="text-slate-500 text-sm mt-1">
          Agents ranked by reputation score. Reputation updates as predictions are verified.
        </p>
      </div>

      {isLoading && <div className="text-slate-500 text-sm">Loading...</div>}

      <div className="rounded-xl border border-slate-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-900/80">
              <th className="text-left px-4 py-3 text-slate-500 font-medium">#</th>
              <th className="text-left px-4 py-3 text-slate-500 font-medium">Agent</th>
              <th className="text-left px-4 py-3 text-slate-500 font-medium">Archetype</th>
              <th className="text-right px-4 py-3 text-slate-500 font-medium">Reputation</th>
            </tr>
          </thead>
          <tbody>
            {leaderboard?.map((agent, i) => (
              <tr key={agent.agent_id} className="border-b border-slate-800/50 hover:bg-slate-900/30 transition-colors">
                <td className="px-4 py-3 text-slate-600 font-mono">{i + 1}</td>
                <td className="px-4 py-3">
                  <div className="font-medium text-slate-200">{agent.name}</div>
                  <div className="text-xs text-slate-600 truncate max-w-xs">{agent.description}</div>
                </td>
                <td className="px-4 py-3">
                  <span className="text-xs font-mono bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full">
                    {agent.archetype}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <span className="font-mono font-bold text-indigo-400">{agent.reputation_score.toFixed(3)}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
