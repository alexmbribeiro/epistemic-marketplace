"use client";

import type { Conclusion } from "@/types";
import { asText } from "@/lib/text";

interface Props {
  conclusion: Conclusion;
  mean: number;
}

const CONSENSUS = {
  strong_agreement: { label: "Strong agreement", ring: "border-emerald-400/25", dot: "bg-emerald-300", text: "text-emerald-200/80" },
  leaning: { label: "Leaning", ring: "border-cyan-400/25", dot: "bg-cyan-300", text: "text-cyan-200/80" },
  contested: { label: "Contested", ring: "border-amber-400/25", dot: "bg-amber-300", text: "text-amber-200/80" },
  deadlocked: { label: "Deadlocked", ring: "border-rose-400/25", dot: "bg-rose-300", text: "text-rose-200/80" },
} as const;

export default function ConclusionPanel({ conclusion, mean }: Props) {
  const c = CONSENSUS[conclusion.consensus] ?? CONSENSUS.contested;

  return (
    <div className={`glass border ${c.ring} p-7 space-y-5`}>
      <div className="flex items-center gap-2">
        <span className={`w-2 h-2 rounded-full ${c.dot}`} />
        <h2 className="eyebrow">Conclusion</h2>
        <span className={`text-xs ${c.text}`}>{c.label}</span>
        <span className="ml-auto font-mono text-sm text-white/55">
          {Math.round(mean * 100)}% mean belief
        </span>
      </div>

      <p className="text-[19px] leading-[1.55] text-white/90 tracking-[-0.015em]">{asText(conclusion.verdict)}</p>
      <p className="text-sm text-white/55 leading-relaxed">{asText(conclusion.reasoning)}</p>

      {conclusion.what_would_settle_it?.length > 0 && (
        <div className="space-y-1.5 pt-1">
          <p className="text-xs text-white/40">What would settle it</p>
          <ul className="space-y-1.5">
            {conclusion.what_would_settle_it.map((x, i) => (
              <li key={i} className="text-sm text-white/75 flex gap-2">
                <span className="text-white/28 shrink-0 font-mono text-xs mt-0.5">
                  {String(i + 1).padStart(2, "0")}
                </span>
                {asText(x)}
              </li>
            ))}
          </ul>
        </div>
      )}

      {!conclusion.generated && (
        <p className="text-xs text-white/28 italic pt-1">
          Synthesis call failed — this summary was computed from the numbers alone.
        </p>
      )}
    </div>
  );
}
