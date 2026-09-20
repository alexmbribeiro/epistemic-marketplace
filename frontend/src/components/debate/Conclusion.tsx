"use client";

import type { Conclusion } from "@/types";
import { asText } from "@/lib/text";

interface Props {
  conclusion: Conclusion;
  weightedMean: number;
}

const CONSENSUS = {
  strong_agreement: { label: "Strong agreement", ring: "border-emerald-600/50", dot: "bg-emerald-400", text: "text-emerald-300" },
  leaning: { label: "Leaning", ring: "border-cyan-600/50", dot: "bg-cyan-400", text: "text-cyan-300" },
  contested: { label: "Contested", ring: "border-amber-600/50", dot: "bg-amber-400", text: "text-amber-300" },
  deadlocked: { label: "Deadlocked", ring: "border-rose-600/50", dot: "bg-rose-400", text: "text-rose-300" },
} as const;

export default function ConclusionPanel({ conclusion, weightedMean }: Props) {
  const c = CONSENSUS[conclusion.consensus] ?? CONSENSUS.contested;

  return (
    <div className={`rounded-xl border ${c.ring} bg-slate-900/60 p-5 space-y-4`}>
      <div className="flex items-center gap-2">
        <span className={`w-2 h-2 rounded-full ${c.dot}`} />
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Conclusion</h2>
        <span className={`text-xs ${c.text}`}>{c.label}</span>
        <span className="ml-auto font-mono text-sm text-slate-400">
          {Math.round(weightedMean * 100)}% weighted belief
        </span>
      </div>

      <p className="text-base text-slate-100 leading-relaxed">{asText(conclusion.verdict)}</p>
      <p className="text-sm text-slate-400 leading-relaxed">{asText(conclusion.reasoning)}</p>

      {conclusion.what_would_settle_it?.length > 0 && (
        <div className="space-y-1.5 pt-1">
          <p className="text-xs text-slate-500">What would settle it</p>
          <ul className="space-y-1.5">
            {conclusion.what_would_settle_it.map((x, i) => (
              <li key={i} className="text-sm text-slate-300 flex gap-2">
                <span className="text-slate-600 shrink-0 font-mono text-xs mt-0.5">
                  {String(i + 1).padStart(2, "0")}
                </span>
                {asText(x)}
              </li>
            ))}
          </ul>
        </div>
      )}

      {!conclusion.generated && (
        <p className="text-xs text-slate-600 italic pt-1">
          Synthesis call failed — this summary was computed from the numbers alone.
        </p>
      )}
    </div>
  );
}
