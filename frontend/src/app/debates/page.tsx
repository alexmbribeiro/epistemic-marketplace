"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { debatesApi } from "@/lib/api";
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

function Mean({ value, size = "lg" }: { value: number | null; size?: "lg" | "sm" }) {
  if (value === null) return null;
  const pct = Math.round(value * 100);
  const tone = pct > 65 ? "text-[#6ea8ea]" : pct < 35 ? "text-[#e88b8b]" : "text-white/70";
  return (
    <span className={`display tabular-nums ${tone} ${size === "lg" ? "text-[26px]" : "text-[17px]"}`}>
      {pct}%
    </span>
  );
}

/** A claim and every debate held on it. */
interface Group {
  claimId: string;
  claim: string;
  category: string | null;
  debates: Debate[];
}

export default function DebatesPage() {
  const [open, setOpen] = useState<string | null>(null);
  const { data: debates, isLoading } = useQuery({
    queryKey: ["debates"],
    queryFn: () => debatesApi.list(100),
    refetchInterval: 10000,
  });

  // The same claim is deliberately run more than once with different rosters,
  // so the list groups by claim: one entry to read, its runs inside.
  const groups: Group[] = [];
  const index = new Map<string, Group>();
  for (const d of debates ?? []) {
    let g = index.get(d.claim_id);
    if (!g) {
      g = {
        claimId: d.claim_id,
        claim: d.claim_content ?? "Untitled claim",
        category: d.claim_category,
        debates: [],
      };
      index.set(d.claim_id, g);
      groups.push(g);
    }
    g.debates.push(d);
  }

  return (
    <div className="space-y-7">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="display text-[28px] text-white/90">Debates</h1>
          <p className="text-white/40 text-[14px] mt-1">
            Grouped by claim. A claim run more than once was argued by different agents each time.
          </p>
        </div>
        <Link
          href="/"
          className="glass-sm glass-interactive pill px-4 py-2 text-[13px] text-white/70 whitespace-nowrap"
        >
          New debate
        </Link>
      </div>

      {isLoading && <div className="text-white/30 text-sm">Loading…</div>}

      <div className="space-y-3">
        {groups.map((g) => {
          const single = g.debates.length === 1;
          const isOpen = open === g.claimId;
          const means = g.debates
            .map((d) => d.final_belief_distribution?.mean)
            .filter((m): m is number => typeof m === "number");
          const spread =
            means.length > 1 ? Math.round((Math.max(...means) - Math.min(...means)) * 100) : null;

          // A single run needs no shelf to sit on — link straight to it.
          if (single) {
            return (
              <Link key={g.claimId} href={`/debates/${g.debates[0].id}`}>
                <div className="glass glass-interactive p-5 flex items-center gap-4">
                  <div className="flex-1 min-w-0">
                    <p className="text-[15px] text-white/85 leading-snug">{g.claim}</p>
                    <div className="flex items-center gap-2.5 mt-2">
                      <StatusBadge status={g.debates[0].status} />
                      {g.category && <span className="text-[11px] text-white/30">{g.category}</span>}
                      <span className="text-[11px] text-white/25">
                        {g.debates[0].agent_ids.length} agents
                      </span>
                    </div>
                  </div>
                  <Mean value={g.debates[0].final_belief_distribution?.mean ?? null} />
                </div>
              </Link>
            );
          }

          return (
            <div key={g.claimId} className={`glass p-5 ${isOpen ? "" : "glass-interactive"}`}>
              <button
                type="button"
                onClick={() => setOpen(isOpen ? null : g.claimId)}
                aria-expanded={isOpen}
                className="w-full flex items-center gap-4 text-left"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-[15px] text-white/85 leading-snug">{g.claim}</p>
                  <div className="flex items-center gap-2.5 mt-2">
                    <span className="text-[11px] text-white/45">{g.debates.length} runs</span>
                    {g.category && <span className="text-[11px] text-white/30">{g.category}</span>}
                    {spread !== null && (
                      <span className="text-[11px] text-white/30">
                        {spread === 0 ? "same verdict both times" : `${spread}pt${spread === 1 ? "" : "s"} apart`}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-baseline gap-2 shrink-0">
                  {means.map((m, i) => (
                    <span key={i} className="flex items-baseline gap-2">
                      {i > 0 && <span className="text-white/20 text-[13px]">·</span>}
                      <Mean value={m} size="sm" />
                    </span>
                  ))}
                </div>
                <span
                  className={`text-white/25 shrink-0 transition-transform ${isOpen ? "rotate-90" : ""}`}
                >
                  ›
                </span>
              </button>

              {isOpen && (
                <div className="pt-4 mt-4 border-t border-white/[0.07] space-y-2">
                  {g.debates.map((d, i) => (
                    <Link key={d.id} href={`/debates/${d.id}`}>
                      <div className="glass-sm glass-interactive p-3.5 flex items-center gap-3">
                        <span className="text-[11px] text-white/30 font-mono w-10 shrink-0">
                          run {i + 1}
                        </span>
                        <StatusBadge status={d.status} />
                        <span className="text-[11px] text-white/25">
                          {d.agent_ids.length} agents
                        </span>
                        <span className="text-[11px] text-white/25">
                          {new Date(d.created_at).toLocaleDateString()}
                        </span>
                        <span className="flex-1" />
                        <Mean value={d.final_belief_distribution?.mean ?? null} size="sm" />
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          );
        })}

        {!isLoading && !groups.length && (
          <div className="text-center py-16 text-white/28">
            No debates yet.{" "}
            <Link href="/" className="text-white/60 hover:text-white/90 underline">
              Start one
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
