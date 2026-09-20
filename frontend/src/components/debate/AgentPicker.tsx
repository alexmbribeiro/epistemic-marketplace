"use client";

import { useEffect, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { agentsApi } from "@/lib/api";
import { agentColor } from "@/lib/agentColors";

/** The six seeded archetypes. Anything else is opt-in. */
const DEFAULT_ARCHETYPES = [
  "bayesian",
  "falsificationist",
  "analogist",
  "contrarian",
  "dialectician",
  "frequentist",
];

interface Props {
  selected: string[];
  onChange: (ids: string[]) => void;
}

export default function AgentPicker({ selected, onChange }: Props) {
  const { data: agents, isLoading } = useQuery({
    queryKey: ["agents"],
    queryFn: agentsApi.list,
  });

  // Preselect the default six once, when the list first arrives. After that
  // the selection belongs to the user — including an empty one, which is why
  // this cannot just be "if selected is empty, use the defaults".
  const seeded = useRef(false);
  useEffect(() => {
    if (seeded.current || !agents?.length) return;
    seeded.current = true;
    onChange(agents.filter((a) => DEFAULT_ARCHETYPES.includes(a.archetype)).map((a) => a.id));
  }, [agents, onChange]);

  if (isLoading) {
    return <p className="text-xs text-slate-600">Loading agents…</p>;
  }
  if (!agents?.length) {
    return <p className="text-xs text-rose-400">No agents available.</p>;
  }

  const toggle = (id: string) => {
    onChange(selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id]);
  };

  return (
    <div className="space-y-2">
      <div className="flex items-baseline gap-2">
        <label className="text-xs text-slate-500">Agents in this debate</label>
        <span className="text-xs text-slate-600">
          {selected.length} selected{selected.length < 2 ? " — pick at least two" : ""}
        </span>
        <button
          type="button"
          onClick={() =>
            onChange(
              selected.length === agents.length
                ? agents.filter((a) => DEFAULT_ARCHETYPES.includes(a.archetype)).map((a) => a.id)
                : agents.map((a) => a.id)
            )
          }
          className="ml-auto text-xs text-indigo-400 hover:text-indigo-300"
        >
          {selected.length === agents.length ? "Reset to default six" : "Select all"}
        </button>
      </div>

      <div className="flex flex-wrap gap-2">
        {agents.map((a) => {
          const on = selected.includes(a.id);
          const color = agentColor(a.archetype);
          return (
            <button
              key={a.id}
              type="button"
              onClick={() => toggle(a.id)}
              title={a.description}
              aria-pressed={on}
              className={`flex items-center gap-2 text-xs rounded-full border px-3 py-1.5 transition-colors ${
                on
                  ? "border-slate-500 bg-slate-800 text-slate-100"
                  : "border-slate-800 bg-transparent text-slate-500 hover:border-slate-700"
              }`}
            >
              <span
                className="w-2 h-2 rounded-full shrink-0"
                style={{ background: on ? color : "transparent", border: `1px solid ${color}` }}
              />
              {a.name}
            </button>
          );
        })}
      </div>
    </div>
  );
}
