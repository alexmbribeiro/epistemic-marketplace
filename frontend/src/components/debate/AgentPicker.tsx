"use client";

import { useEffect, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { agentsApi } from "@/lib/api";
import { MAX_SERIES, paletteFor } from "@/lib/agentColors";

/** Mirrors DEFAULT_ARCHETYPES on the backend: five debating leaves three to judge. */
const DEFAULT_ARCHETYPES = [
  "nietzschean",
  "humean",
  "kantian",
  "aristotelian",
  "jungian",
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
    return <p className="text-xs text-white/28">Loading agents…</p>;
  }
  if (!agents?.length) {
    return <p className="text-xs text-rose-400">No agents available.</p>;
  }

  // Only selected agents carry colour, assigned in selection order. There are
  // more agents than validated slots, so this shows exactly the colours the
  // debate will use — and nothing has to be invented for the rest.
  const byId = new Map(agents.map((a) => [a.id, a]));
  const palette = paletteFor(
    selected.flatMap((id) => {
      const agent = byId.get(id);
      return agent ? [agent.archetype] : [];
    })
  );

  const toggle = (id: string) => {
    onChange(selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id]);
  };

  return (
    <div className="space-y-2">
      <div className="flex items-baseline gap-2">
        <label className="text-xs text-white/40">Agents in this debate</label>
        <span className="text-xs text-white/28">
          {selected.length} selected
          {selected.length < 2
            ? " — pick at least two"
            : selected.length > MAX_SERIES
            ? ` — at most ${MAX_SERIES}`
            : ""}
        </span>
        <button
          type="button"
          onClick={() =>
            onChange(agents.filter((a) => DEFAULT_ARCHETYPES.includes(a.archetype)).map((a) => a.id))
          }
          className="ml-auto text-xs text-indigo-400 hover:text-indigo-300"
        >
          Reset to default five
        </button>
      </div>

      <div className="flex flex-wrap gap-2">
        {agents.map((a) => {
          const on = selected.includes(a.id);
          const color = palette[a.archetype];
          return (
            <button
              key={a.id}
              type="button"
              onClick={() => toggle(a.id)}
              title={a.description}
              aria-pressed={on}
              className={`flex items-center gap-2 text-[13px] pill border px-3.5 py-2 transition-all ${
                on
                  ? "border-white/25 bg-white/[0.09] text-white/90"
                  : "border-white/[0.08] bg-transparent text-white/40 hover:border-white/15"
              }`}
            >
              <span
                className="w-2 h-2 rounded-full shrink-0"
                style={{
                  background: on ? color : "transparent",
                  border: `1px solid ${on ? color : "#475569"}`,
                }}
              />
              {a.name}
            </button>
          );
        })}
      </div>
    </div>
  );
}
