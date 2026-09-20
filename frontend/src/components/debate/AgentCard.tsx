"use client";

import type { AgentPosition, ArchetypeId } from "@/types";
import { asText } from "@/lib/text";
import { colorFrom } from "@/lib/agentColors";


function BeliefBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color = score > 0.6 ? "bg-cyan-400" : score < 0.4 ? "bg-rose-400" : "bg-amber-400";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-white/10 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-700 ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-sm font-mono font-bold w-10 text-right">{pct}%</span>
    </div>
  );
}

interface AgentCardProps {
  position: AgentPosition;
  isLatest?: boolean;
  /** Assigned per debate — see lib/agentColors. */
  palette: Record<string, string>;
}

export default function AgentCard({ position, isLatest = true, palette }: AgentCardProps) {
  // Same colour the agent carries in the trajectory chart and the exchanges,
  // so identity reads the same everywhere.
  const color = colorFrom(palette, position.archetype);

  return (
    <div
      className={`rounded-xl border border-white/[0.08] border-l-4 bg-white/[0.03] p-4 space-y-3 transition-all ${
        isLatest ? "opacity-100" : "opacity-50"
      }`}
      style={{ borderLeftColor: color }}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-white">{position.agent_name}</span>
          <span
            className="text-xs px-2 py-0.5 rounded-full font-mono text-white/75 border"
            style={{ borderColor: color }}
          >
            {position.archetype}
          </span>
          <span className="text-xs text-white/40">R{position.round_number}</span>
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

      <p className="text-sm text-white/75 italic">"{position.argument_content}"</p>

      {position.cruxes.length > 0 && (
        <div>
          <p className="text-xs text-white/40 mb-1">What would change my mind:</p>
          <ul className="space-y-1">
            {position.cruxes.slice(0, 2).map((c, i) => (
              <li key={i} className="text-xs text-white/55 flex gap-1">
                <span className="text-amber-500 shrink-0">→</span>
                {asText(c)}
              </li>
            ))}
          </ul>
        </div>
      )}

      {position.unanswered_questions.length > 0 && (
        <div>
          <p className="text-xs text-white/40 mb-1">Cannot answer:</p>
          <ul className="space-y-1">
            {position.unanswered_questions.slice(0, 1).map((q, i) => (
              <li key={i} className="text-xs text-rose-400/80 flex gap-1">
                <span className="shrink-0">?</span>
                {asText(q)}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
