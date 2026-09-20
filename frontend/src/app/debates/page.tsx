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
    initializing: "bg-white/[0.07] text-white/55",
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
        <h1 className="text-2xl font-bold text-white/90">Debates</h1>
        <Link
          href="/"
          className="text-sm bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg transition-colors"
        >
          New Debate →
        </Link>
      </div>

      {isLoading && <div className="text-white/40 text-sm">Loading debates...</div>}

      <div className="space-y-3">
        {debates?.map((debate) => (
          <DebateRow key={debate.id} debate={debate} />
        ))}
        {!isLoading && !debates?.length && (
          <div className="text-center py-16 text-white/28">
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
      <div className="glass glass-interactive p-5 flex items-center gap-4">
        <div className="flex-1 min-w-0">
          <p className="text-sm text-white/75 truncate font-mono text-xs text-white/40">{debate.claim_id}</p>
          <div className="flex items-center gap-2 mt-1">
            <StatusBadge status={debate.status} />
            <span className="text-xs text-white/28">{new Date(debate.created_at).toLocaleDateString()}</span>
            {debate.agent_ids.length > 0 && (
              <span className="text-xs text-white/28">{debate.agent_ids.length} agents</span>
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
            <div className="text-xs text-white/28">consensus</div>
          </div>
        )}
      </div>
    </Link>
  );
}
