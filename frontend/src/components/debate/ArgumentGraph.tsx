"use client";

import { useMemo, useState } from "react";
import type { ArgumentGraph } from "@/types";

/**
 * A layered reading of the debate, not a force graph.
 *
 * The data is already layered: every agent has one node per round, joined in
 * sequence, and challenges cross between agents. A force simulation throws
 * that away and settles into a hairball where the one thing worth seeing —
 * who answered whom — is exactly what gets buried. So rounds are columns,
 * agents are rows, each agent's own track runs straight across, and the only
 * diagonals on the canvas are the challenges.
 *
 * Rows are ordered by final belief, so the chart reads top-affirms to
 * bottom-doubts and the fault line is where the colour turns.
 */

const EDGE_STYLE: Record<string, { color: string; label: string }> = {
  contradicts: { color: "#e66767", label: "contradicts" },
  qualifies: { color: "#c98500", label: "qualifies" },
  redefines: { color: "#9085e9", label: "redefines" },
  supports: { color: "#3987e5", label: "supports" },
  uncertain: { color: "rgba(255,255,255,0.35)", label: "uncertain" },
};

// Same diverging ramp as the belief distribution: false and true poles
// meeting at a neutral grey.
const BELIEF_RAMP = ["#e66767", "#b47a86", "#6f7681", "#4a7cbd", "#3987e5"];
function beliefColor(score?: number) {
  if (score === undefined || score === null) return "rgba(255,255,255,0.15)";
  return BELIEF_RAMP[Math.min(Math.floor(score * 5), 4)];
}

const ROUND_LABELS = ["Independent", "Cross-challenge", "Synthesis"];

const GUTTER = 118;
const ROW_H = 54;
const HEADER_H = 40;
const PAD_R = 28;

interface Props {
  graph: ArgumentGraph;
}

export default function ArgumentGraphViz({ graph }: Props) {
  const [hovered, setHovered] = useState<string | null>(null);
  const [tip, setTip] = useState<{ x: number; y: number; text: string } | null>(null);

  const model = useMemo(() => {
    const positions = graph.nodes.filter((n) => n.type !== "claim");
    if (!positions.length) return null;

    const rounds = Math.max(...positions.map((n) => Number(n.round) || 1));

    // Agent identity lives in the node id as `${agent_id}_r${round}`.
    const agents = new Map<string, { name: string; archetype: string; finals: number }>();
    for (const n of positions) {
      const agentId = String(n.id).replace(/_r\d+$/, "");
      const name = String(n.label ?? "").split(" (")[0];
      const entry = agents.get(agentId) ?? { name, archetype: String(n.archetype ?? ""), finals: 0.5 };
      if (Number(n.round) === rounds) entry.finals = Number(n.belief_score ?? 0.5);
      agents.set(agentId, entry);
    }

    const order = Array.from(agents.entries()).sort((a, b) => b[1].finals - a[1].finals);
    const rowOf = new Map(order.map(([id], i) => [id, i]));

    const nodeAt = new Map(
      positions.map((n) => [String(n.id), { ...n, agentId: String(n.id).replace(/_r\d+$/, "") }])
    );

    return { rounds, order, rowOf, nodeAt, positions };
  }, [graph]);

  if (!model) return null;

  const { rounds, order, rowOf, nodeAt } = model;
  const width = 860;
  const colW = (width - GUTTER - PAD_R) / rounds;
  const height = HEADER_H + order.length * ROW_H + 16;
  const x = (round: number) => GUTTER + colW * (round - 0.5);
  const y = (row: number) => HEADER_H + row * ROW_H + ROW_H / 2;

  const pos = (id: string) => {
    const n = nodeAt.get(id);
    if (!n) return null;
    const row = rowOf.get(n.agentId);
    if (row === undefined) return null;
    return { x: x(Number(n.round) || 1), y: y(row), node: n };
  };

  const challenges = graph.edges.filter((e) => e.type !== "updates" && nodeAt.has(String(e.source)));
  const activeAgent = hovered;

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-[11px]">
        {Object.entries(EDGE_STYLE).map(([k, v]) => (
          <span key={k} className="flex items-center gap-1.5">
            <span className="w-4 h-[2px] rounded" style={{ background: v.color }} />
            <span className="text-white/45">{v.label}</span>
          </span>
        ))}
        <span className="text-white/25 ml-auto">hover a name to isolate its thread</span>
      </div>

      <div className="relative overflow-x-auto">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full" style={{ minWidth: 640 }}>
          {/* Round headers */}
          {Array.from({ length: rounds }, (_, i) => (
            <g key={i}>
              <text x={x(i + 1)} y={16} textAnchor="middle" fontSize={11} fill="rgba(255,255,255,0.5)">
                Round {i + 1}
              </text>
              <text x={x(i + 1)} y={30} textAnchor="middle" fontSize={10} fill="rgba(255,255,255,0.25)">
                {ROUND_LABELS[i]}
              </text>
            </g>
          ))}

          {/* The claim, as a spine everything departs from */}
          <line
            x1={GUTTER - 14}
            y1={HEADER_H + 4}
            x2={GUTTER - 14}
            y2={height - 12}
            stroke="rgba(255,255,255,0.18)"
            strokeWidth={2}
          />
          <text
            x={GUTTER - 22}
            y={HEADER_H + 4}
            textAnchor="end"
            fontSize={10}
            fill="rgba(255,255,255,0.3)"
          >
            CLAIM
          </text>

          {order.map(([agentId, a], row) => {
            const dim = activeAgent !== null && activeAgent !== agentId;
            return (
              <g key={agentId} opacity={dim ? 0.18 : 1} style={{ transition: "opacity 140ms" }}>
                {/* Track: the agent's own line across the rounds */}
                <line
                  x1={GUTTER - 14}
                  y1={y(row)}
                  x2={x(rounds)}
                  y2={y(row)}
                  stroke="rgba(255,255,255,0.10)"
                  strokeWidth={1}
                />
                <text
                  x={GUTTER - 30}
                  y={y(row) + 4}
                  textAnchor="end"
                  fontSize={12}
                  fill={activeAgent === agentId ? "rgba(255,255,255,0.95)" : "rgba(255,255,255,0.6)"}
                  style={{ cursor: "pointer" }}
                  onMouseEnter={() => setHovered(agentId)}
                  onMouseLeave={() => setHovered(null)}
                >
                  {a.name}
                </text>
              </g>
            );
          })}

          {/* Challenges: the only diagonals on the canvas */}
          {challenges.map((e) => {
            const from = pos(String(e.source));
            const to = pos(String(e.target));
            if (!from || !to) return null;
            const style = EDGE_STYLE[e.type] ?? EDGE_STYLE.uncertain;
            const involved = from.node.agentId === activeAgent || to.node.agentId === activeAgent;
            const dim = activeAgent !== null && !involved;
            const mx = (from.x + to.x) / 2;
            const bow = Math.sign(to.y - from.y || 1) * 14;
            const text = String(
              (e as unknown as { challenge_text?: string }).challenge_text ?? e.label ?? e.type
            );
            return (
              <path
                key={e.id}
                d={`M ${from.x} ${from.y} Q ${mx} ${(from.y + to.y) / 2 + bow} ${to.x} ${to.y}`}
                fill="none"
                stroke={style.color}
                strokeWidth={activeAgent && involved ? 2.4 : 1.6}
                opacity={dim ? 0.08 : 0.85}
                markerEnd={`url(#tip-${e.type})`}
                style={{ transition: "opacity 140ms", cursor: "pointer" }}
                onMouseEnter={(ev) =>
                  setTip({ x: ev.nativeEvent.offsetX, y: ev.nativeEvent.offsetY, text })
                }
                onMouseLeave={() => setTip(null)}
              />
            );
          })}

          {/* Positions */}
          {model.positions.map((n) => {
            const p = pos(String(n.id));
            if (!p) return null;
            const dim = activeAgent !== null && activeAgent !== p.node.agentId;
            return (
              <g key={String(n.id)} opacity={dim ? 0.18 : 1} style={{ transition: "opacity 140ms" }}>
                <circle
                  cx={p.x}
                  cy={p.y}
                  r={11}
                  fill={beliefColor(Number(n.belief_score))}
                  stroke="#05070b"
                  strokeWidth={2}
                />
                <text
                  x={p.x}
                  y={p.y + 3.5}
                  textAnchor="middle"
                  fontSize={9}
                  fill="rgba(255,255,255,0.9)"
                  pointerEvents="none"
                >
                  {Math.round(Number(n.belief_score ?? 0) * 100)}
                </text>
              </g>
            );
          })}

          <defs>
            {Object.entries(EDGE_STYLE).map(([k, v]) => (
              <marker
                key={k}
                id={`tip-${k}`}
                viewBox="0 -4 8 8"
                refX={14}
                refY={0}
                markerWidth={5}
                markerHeight={5}
                orient="auto"
              >
                <path d="M0,-4L8,0L0,4" fill={v.color} />
              </marker>
            ))}
          </defs>
        </svg>

        {tip && (
          <div
            className="glass-sm absolute z-10 max-w-sm px-3 py-2 text-[12px] leading-relaxed text-white/75 pointer-events-none"
            style={{ left: Math.min(tip.x + 12, 520), top: tip.y + 12 }}
          >
            {tip.text}
          </div>
        )}
      </div>
    </div>
  );
}
