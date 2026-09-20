"use client";

import { useQuery } from "@tanstack/react-query";
import { debatesApi, claimsApi } from "@/lib/api";
import Link from "next/link";
import type { Debate } from "@/types";

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    completed: "bg-emerald-900 text-emerald-300",
    debating: "bg-indigo-900 text-indigo-300",
    failed: "bg-rose-900 text-rose-300",
    initializing: "bg-slate-800 text-slate-400",
  };
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-mono ${styles[status] || styles.initializing}`}>
      {status}
    </span>
  );
}

export default function DebatesPage() {
  const { data: debates, isLoading } = useQuery({
    queryKey: ["debates"],
    queryFn: () => debatesApi.list(),
    refetchInterval: 10000,
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-100">Debates</h1>
        <Link
          href="/"
          className="text-sm bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg transition-colors"
        >
          New Debate →
        </Link>
      </div>

      {isLoading && <div className="text-slate-500 text-sm">Loading debates...</div>}

      <div className="space-y-3">
        {debates?.map((debate) => (
          <DebateRow key={debate.id} debate={debate} />
        ))}
        {!isLoading && !debates?.length && (
          <div className="text-center py-16 text-slate-600">
            No debates yet.{" "}
            <Link href="/" className="text-indigo-400 hover:underline">
              Start one →
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}

function DebateRow({ debate }: { debate: Debate }) {
  const dist = debate.final_belief_distribution;
  const meanPct = dist ? Math.round(dist.weighted_mean * 100) : null;

  return (
    <Link href={`/debates/${debate.id}`}>
      <div className="rounded-xl border border-slate-800 bg-slate-900/50 hover:border-indigo-800 hover:bg-slate-900 transition-all p-4 flex items-center gap-4">
        <div className="flex-1 min-w-0">
          <p className="text-sm text-slate-300 truncate font-mono text-xs text-slate-500">{debate.claim_id}</p>
          <div className="flex items-center gap-2 mt-1">
            <StatusBadge status={debate.status} />
            <span className="text-xs text-slate-600">{new Date(debate.created_at).toLocaleDateString()}</span>
            {debate.agent_ids.length > 0 && (
              <span className="text-xs text-slate-600">{debate.agent_ids.length} agents</span>
            )}
          </div>
        </div>
        {meanPct !== null && (
          <div className="text-right">
            <div
              className={`text-2xl font-bold font-mono ${
                meanPct > 65 ? "text-cyan-400" : meanPct < 35 ? "text-rose-400" : "text-amber-400"
              }`}
            >
              {meanPct}%
            </div>
            <div className="text-xs text-slate-600">consensus</div>
          </div>
        )}
      </div>
    </Link>
  );
}
