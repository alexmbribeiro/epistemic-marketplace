"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { agentsApi } from "@/lib/api";
import type { StatRow } from "@/types";

function Rows({ label, rows, unit = "" }: { label: string; rows: StatRow[]; unit?: string }) {
  if (!rows?.length) return null;
  return (
    <div className="space-y-1.5">
      <p className="text-[11px] text-white/30">{label}</p>
      {rows.map((r) => (
        <div key={r.name} className="flex items-baseline gap-2 text-[13px]">
          <span className="text-white/70">{r.name}</span>
          <span className="flex-1 border-b border-dotted border-white/10 translate-y-[-3px]" />
          <span className="tabular-nums text-white/50">
            {r.value}
            {unit}
          </span>
          <span className="text-[11px] text-white/20 tabular-nums w-7 text-right">n={r.n}</span>
        </div>
      ))}
    </div>
  );
}

function Detail({ agentId }: { agentId: string }) {
  const { data: s, isLoading } = useQuery({
    queryKey: ["agent-stats", agentId],
    queryFn: () => agentsApi.stats(agentId),
  });

  if (isLoading) return <p className="text-[13px] text-white/30 pt-4">Loading…</p>;
  if (!s) return null;

  const d = s.disposition;
  const hasAny =
    s.criteria || s.agrees_most_with.length || s.rated_best_by.length || d.mean_belief !== null;

  return (
    <div className="pt-5 mt-5 border-t border-white/[0.07] space-y-6">
      <p className="text-[14px] leading-relaxed text-white/60 max-w-2xl">{s.description}</p>

      {!hasAny ? (
        <p className="text-[13px] text-white/30">
          No statistics yet — this agent has not been through a debate.
        </p>
      ) : (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              ["Elo", s.provisional ? `${s.elo_rating.toFixed(0)}*` : s.elo_rating.toFixed(0)],
              ["Debated", String(s.debates)],
              ["Judged", String(s.judged)],
              [
                "Mean belief",
                d.mean_belief === null ? "—" : `${Math.round(d.mean_belief * 100)}%`,
              ],
            ].map(([k, v]) => (
              <div key={k} className="glass-sm p-3.5">
                <div className="text-[11px] text-white/30">{k}</div>
                <div className="display text-[20px] text-white/85 tabular-nums mt-0.5">{v}</div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-10 gap-y-6">
            <Rows label="Lands closest to" rows={s.agrees_most_with} />
            <Rows label="Furthest from" rows={s.disagrees_most_with} />
            <Rows label="Scores best by" rows={s.rated_best_by} />
            <Rows label="Scores worst by" rows={s.rated_worst_by} />
            <Rows label="Is generous towards" rows={s.rates_highest} />
            <Rows label="Is hardest on" rows={s.rates_lowest} />
          </div>

          {s.criteria && (
            <div className="space-y-2">
              <p className="text-[11px] text-white/30">Craft, as scored by peers</p>
              {(
                [
                  ["Method fidelity", s.criteria.method_fidelity],
                  ["Engagement", s.criteria.engagement],
                  ["Crux quality", s.criteria.crux_quality],
                  ["Responsiveness", s.criteria.responsiveness],
                ] as const
              ).map(([k, v]) => (
                <div key={k} className="flex items-center gap-3">
                  <span className="text-[13px] text-white/55 w-32 shrink-0">{k}</span>
                  <span className="flex-1 h-1.5 rounded-full bg-white/[0.07] overflow-hidden">
                    <span
                      className="block h-full rounded-full bg-white/45"
                      style={{ width: `${v}%` }}
                    />
                  </span>
                  <span className="text-[13px] tabular-nums text-white/50 w-8 text-right">
                    {v.toFixed(0)}
                  </span>
                </div>
              ))}
            </div>
          )}

          <div className="flex flex-wrap gap-x-8 gap-y-2 text-[12px] text-white/35">
            {d.mean_distance_from_room !== null && (
              <span>
                Sits {Math.round(d.mean_distance_from_room * 100)}pts from the rest of the room on
                average
              </span>
            )}
            {d.mean_swing !== null && (
              <span>Travels {Math.round(d.mean_swing * 100)}pts across three rounds</span>
            )}
          </div>

          {s.provisional && (
            <p className="text-[12px] text-white/25">
              * Fewer than five rated debates — every figure here is a small sample.
            </p>
          )}
        </>
      )}
    </div>
  );
}

export default function MarketplacePage() {
  const [open, setOpen] = useState<string | null>(null);
  const { data: agents, isLoading } = useQuery({ queryKey: ["agents"], queryFn: agentsApi.list });

  return (
    <div className="space-y-7">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="display text-[28px] text-white/90">Agents</h1>
          <p className="text-white/40 text-[14px] mt-1">
            Each reasons by a method of its own, and declares where that method fails.
          </p>
        </div>
        <Link
          href="/marketplace/create"
          className="glass-sm glass-interactive pill px-4 py-2 text-[13px] text-white/70 whitespace-nowrap"
        >
          New agent
        </Link>
      </div>

      {isLoading && <p className="text-white/30 text-sm">Loading…</p>}

      <div className="space-y-3">
        {agents?.map((a) => {
          const isOpen = open === a.id;
          return (
            <div key={a.id} className={`glass p-5 ${isOpen ? "" : "glass-interactive"}`}>
              <button
                type="button"
                onClick={() => setOpen(isOpen ? null : a.id)}
                aria-expanded={isOpen}
                className="w-full flex items-center gap-4 text-left"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2.5">
                    <span className="text-[15px] font-medium text-white/90">{a.name}</span>
                    <span className="text-[11px] text-white/30 font-mono">{a.archetype}</span>
                  </div>
                  {!isOpen && (
                    <p className="text-[13px] text-white/40 mt-1 truncate">{a.description}</p>
                  )}
                </div>
                <span className="tabular-nums text-[14px] text-white/55 shrink-0">
                  {a.elo_rating?.toFixed(0) ?? "—"}
                </span>
                <span
                  className={`text-white/25 shrink-0 transition-transform ${isOpen ? "rotate-90" : ""}`}
                >
                  ›
                </span>
              </button>
              {isOpen && <Detail agentId={a.id} />}
            </div>
          );
        })}
      </div>
    </div>
  );
}
