"use client";

import { useQuery } from "@tanstack/react-query";
import { debatesApi, claimsApi } from "@/lib/api";
import Link from "next/link";
import type { Debate } from "@/types";

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    completed: "bg-emerald-400/10 text-emerald-200/80 border border-emerald-400/20",
    debating: "bg-indigo-400/10 text-indigo-200/80 border border-indigo-400/20",
    failed: "bg-rose-400/10 text-rose-200/80 border border-rose-400/20",
    initializing: "bg-white/[0.06] text-white/45 border border-white/10",
  };
  return (
    <span className={`text-[11px] px-2 py-0.5 pill ${styles[status] || styles.initializing}`}>
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
          className="glass-sm glass-interactive pill px-4 py-2 text-[13px] text-white/70 whitespace-nowrap"
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
  const meanPct = dist ? Math.round(dist.mean * 100) : null;

  return (
    <Link href={`/debates/${debate.id}`}>
      <div className="glass glass-interactive p-5 flex items-center gap-4">
        <div className="flex-1 min-w-0">
          <p className="text-[15px] text-white/85 leading-snug">
            {debate.claim_content ?? "Untitled claim"}
          </p>
          <div className="flex items-center gap-2.5 mt-2">
            <StatusBadge status={debate.status} />
            {debate.claim_category && (
              <span className="text-[11px] text-white/30">{debate.claim_category}</span>
            )}
            <span className="text-[11px] text-white/25">
              {new Date(debate.created_at).toLocaleDateString()}
            </span>
            {debate.agent_ids.length > 0 && (
              <span className="text-[11px] text-white/25">{debate.agent_ids.length} agents</span>
            )}
          </div>
        </div>
        {meanPct !== null && (
          <div className="text-right">
            <div
              className={`display text-[26px] tabular-nums ${
                meanPct > 65 ? "text-[#6ea8ea]" : meanPct < 35 ? "text-[#e88b8b]" : "text-white/70"
              }`}
            >
              {meanPct}%
            </div>
            <div className="text-[11px] text-white/28">mean belief</div>
          </div>
        )}
      </div>
    </Link>
  );
}
