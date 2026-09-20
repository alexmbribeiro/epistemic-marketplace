"use client";

import type { AgentPosition, ArchetypeId } from "@/types";

const ARCHETYPE_COLORS: Record<ArchetypeId | string, string> = {
  bayesian: "border-violet-500 bg-violet-950/30",
  falsificationist: "border-rose-500 bg-rose-950/30",
  analogist: "border-emerald-500 bg-emerald-950/30",
  contrarian: "border-orange-500 bg-orange-950/30",
  dialectician: "border-cyan-500 bg-cyan-950/30",
  frequentist: "border-blue-500 bg-blue-950/30",
  domain_expert: "border-yellow-500 bg-yellow-950/30",
  custom: "border-slate-500 bg-slate-950/30",
};

const ARCHETYPE_BADGE: Record<ArchetypeId | string, string> = {
  bayesian: "bg-violet-900 text-violet-200",
  falsificationist: "bg-rose-900 text-rose-200",
  analogist: "bg-emerald-900 text-emerald-200",
  contrarian: "bg-orange-900 text-orange-200",
  dialectician: "bg-cyan-900 text-cyan-200",
  frequentist: "bg-blue-900 text-blue-200",
  domain_expert: "bg-yellow-900 text-yellow-200",
  custom: "bg-slate-900 text-slate-200",
};

function BeliefBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color = score > 0.6 ? "bg-cyan-400" : score < 0.4 ? "bg-rose-400" : "bg-amber-400";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-700 ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-sm font-mono font-bold w-10 text-right">{pct}%</span>
    </div>
  );
}

interface AgentCardProps {
  position: AgentPosition;
  isLatest?: boolean;
}

export default function AgentCard({ position, isLatest = true }: AgentCardProps) {
  const borderCls = ARCHETYPE_COLORS[position.archetype] || ARCHETYPE_COLORS.custom;
  const badgeCls = ARCHETYPE_BADGE[position.archetype] || ARCHETYPE_BADGE.custom;

  return (
    <div className={`rounded-xl border p-4 space-y-3 transition-all ${borderCls} ${isLatest ? "opacity-100" : "opacity-50"}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-white">{position.agent_name}</span>
          <span className={`text-xs px-2 py-0.5 rounded-full font-mono ${badgeCls}`}>{position.archetype}</span>
          <span className="text-xs text-slate-500">R{position.round_number}</span>
        </div>
        <span
          className={`text-xs px-2 py-0.5 rounded border font-mono ${
            position.argument_type === "supports"
              ? "border-cyan-600 text-cyan-400"
              : position.argument_type === "contradicts"
              ? "border-rose-600 text-rose-400"
              : "border-amber-600 text-amber-400"
          }`}
        >
          {position.argument_type}
        </span>
      </div>

      <BeliefBar score={position.belief_score} />

      <p className="text-sm text-slate-300 italic">"{position.argument_content}"</p>

      {position.cruxes.length > 0 && (
        <div>
          <p className="text-xs text-slate-500 mb-1">What would change my mind:</p>
          <ul className="space-y-1">
            {position.cruxes.slice(0, 2).map((c, i) => (
              <li key={i} className="text-xs text-slate-400 flex gap-1">
                <span className="text-amber-500 shrink-0">→</span>
                {c}
              </li>
            ))}
          </ul>
        </div>
      )}

      {position.unanswered_questions.length > 0 && (
        <div>
          <p className="text-xs text-slate-500 mb-1">Cannot answer:</p>
          <ul className="space-y-1">
            {position.unanswered_questions.slice(0, 1).map((q, i) => (
              <li key={i} className="text-xs text-rose-400/80 flex gap-1">
                <span className="shrink-0">?</span>
                {q}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
