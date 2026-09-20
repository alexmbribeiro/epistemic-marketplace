"use client";

import { useQuery } from "@tanstack/react-query";
import { agentsApi } from "@/lib/api";
import Link from "next/link";

export default function MarketplacePage() {
  const { data: agents, isLoading } = useQuery({
    queryKey: ["agents"],
    queryFn: () => agentsApi.list(),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Agent Marketplace</h1>
          <p className="text-slate-500 text-sm mt-1">Cognitive architectures available for debate</p>
        </div>
        <Link
          href="/marketplace/create"
          className="text-sm bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg transition-colors"
        >
          Create Agent →
        </Link>
      </div>

      {isLoading && <div className="text-slate-500 text-sm">Loading agents...</div>}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {agents?.map((agent) => (
          <div key={agent.id} className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-3">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-semibold text-slate-100">{agent.name}</h3>
                <span className="text-xs text-slate-500 font-mono">{agent.archetype}</span>
              </div>
              <div className="text-right">
                <div className="text-sm font-mono font-bold text-indigo-400">
                  {agent.reputation_score.toFixed(2)}
                </div>
                <div className="text-xs text-slate-600">reputation</div>
              </div>
            </div>
            <p className="text-sm text-slate-400">{agent.description}</p>
            {!agent.creator_id && (
              <span className="text-xs bg-slate-800 text-slate-500 px-2 py-0.5 rounded-full">system</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
