"use client";

import { asText } from "@/lib/text";

interface Props {
  questions: string[];
}

export default function UnknownUnknowns({ questions }: Props) {
  if (!questions.length) return null;

  return (
    <div className="rounded-xl border border-rose-900/50 bg-rose-950/20 p-4 space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-rose-400 text-lg">?</span>
        <h3 className="text-sm font-semibold text-rose-300">Unknown Unknowns</h3>
        <span className="text-xs text-slate-500 ml-auto">Questions no agent could answer</span>
      </div>
      <ul className="space-y-2">
        {questions.map((q, i) => (
          <li key={i} className="text-sm text-rose-200/70 flex gap-2">
            <span className="text-rose-600 shrink-0 font-mono text-xs mt-0.5">{String(i + 1).padStart(2, "0")}</span>
            {asText(q)}
          </li>
        ))}
      </ul>
    </div>
  );
}
