"use client";

import type { Exchange } from "@/types";
import { asText } from "@/lib/text";
import { colorFrom } from "@/lib/agentColors";

interface Props {
  exchanges: Exchange[];
  palette: Record<string, string>;
}

const TYPE_STYLE: Record<string, string> = {
  contradicts: "text-rose-300 border-rose-500/40",
  qualifies: "text-amber-300 border-amber-500/40",
  redefines: "text-violet-300 border-violet-500/40",
};

export default function Exchanges({ exchanges, palette }: Props) {
  if (!exchanges.length) return null;

  const byRound = exchanges.reduce<Record<number, Exchange[]>>((acc, e) => {
    (acc[e.round] ??= []).push(e);
    return acc;
  }, {});

  return (
    <div className="space-y-5">
      {Object.entries(byRound).map(([round, items]) => (
        <div key={round} className="space-y-2">
          <p className="text-xs text-slate-500 font-mono">Round {round}</p>
          {items.map((e, i) => (
            <div key={i} className="rounded-lg border border-slate-800 bg-slate-900/40 p-3 space-y-1.5">
              <div className="flex items-center gap-2 text-xs flex-wrap">
                <span className="flex items-center gap-1.5">
                  <span
                    className="w-2 h-2 rounded-full shrink-0"
                    style={{ background: colorFrom(palette, e.from_archetype) }}
                  />
                  <span className="text-slate-300 font-medium">{asText(e.from_agent)}</span>
                </span>
                <span className="text-slate-600">→</span>
                <span className="text-slate-400 capitalize">{asText(e.to_agent)}</span>
                <span
                  className={`ml-auto text-[10px] border rounded px-1.5 py-0.5 ${
                    TYPE_STYLE[e.type] ?? "text-slate-400 border-slate-600"
                  }`}
                >
                  {e.type}
                </span>
              </div>
              <p className="text-sm text-slate-300/90 leading-relaxed">{asText(e.text)}</p>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
