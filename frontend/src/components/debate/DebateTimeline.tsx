"use client";

const ROUNDS = [
  { n: 1, label: "Independent Positions", desc: "Each agent forms its view in isolation" },
  { n: 2, label: "Cross-Challenges", desc: "Agents challenge each other's positions" },
  { n: 3, label: "Synthesis", desc: "Final positions after seeing all challenges" },
];

interface Props {
  currentRound: number;
  status: string;
}

export default function DebateTimeline({ currentRound, status }: Props) {
  return (
    <div className="flex items-center gap-2">
      {ROUNDS.map((r, i) => {
        const done = currentRound > r.n || status === "completed";
        const active = currentRound === r.n && status === "debating";

        return (
          <div key={r.n} className="flex items-center gap-2 flex-1">
            <div className="flex flex-col items-center gap-1 flex-1">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all
                  ${done ? "bg-indigo-600 text-white" : active ? "bg-indigo-500 text-white ring-2 ring-indigo-400 ring-offset-2 ring-offset-slate-900" : "bg-slate-800 text-slate-500"}`}
              >
                {done ? "✓" : r.n}
              </div>
              <div className="text-center">
                <p className={`text-xs font-medium ${done || active ? "text-slate-200" : "text-slate-600"}`}>
                  {r.label}
                </p>
                <p className="text-xs text-slate-600 hidden sm:block">{r.desc}</p>
              </div>
            </div>
            {i < ROUNDS.length - 1 && (
              <div className={`flex-1 h-px mb-5 ${currentRound > r.n || status === "completed" ? "bg-indigo-600" : "bg-slate-700"}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}
