"use client";

import { useEffect } from "react";
import { useDebateStore } from "@/store/debate";
import { useDebateWebSocket } from "@/lib/websocket";
import { debatesApi } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import AgentCard from "./AgentCard";
import BeliefDistributionChart from "./BeliefDistribution";
import ArgumentGraphViz from "./ArgumentGraph";
import DebateTimeline from "./DebateTimeline";
import UnknownUnknowns from "./UnknownUnknowns";
import ConclusionPanel from "./Conclusion";
import BeliefTrajectory from "./BeliefTrajectory";
import Exchanges from "./Exchanges";
import type { DebateEvent } from "@/types";

interface Props {
  debateId: string;
}

export default function DebateRoom({ debateId }: Props) {
  const { status, currentRound, positions, finalDistribution, argumentGraph, unknownUnknowns, synthesis, setDebateId, handleEvent, reset } =
    useDebateStore();

  const { data: debate } = useQuery({
    queryKey: ["debate", debateId],
    queryFn: () => debatesApi.get(debateId),
    refetchInterval: status !== "completed" && status !== "failed" ? 5000 : false,
  });

  useEffect(() => {
    reset();
    setDebateId(debateId);
  }, [debateId]);

  useDebateWebSocket(debateId, (event: DebateEvent) => handleEvent(event));

  // Live events fill the store; a completed debate opened fresh has an empty
  // store, so fall back to the rounds persisted with the synthesis.
  const stored = (synthesis || debate?.synthesis || null)?.positions;
  const latestPositions =
    positions.round3.length ? positions.round3
    : positions.round2.length ? positions.round2
    : positions.round1.length ? positions.round1
    : stored?.round3?.length ? stored.round3
    : stored?.round2?.length ? stored.round2
    : stored?.round1 ?? [];

  const isCompleted = status === "completed" || debate?.status === "completed";
  const effectiveDistribution = finalDistribution || debate?.final_belief_distribution;
  const effectiveGraph = argumentGraph || debate?.argument_graph;
  const effectiveUnknowns = unknownUnknowns.length ? unknownUnknowns : debate?.unknown_unknowns || [];
  const effectiveSynthesis = synthesis || debate?.synthesis || null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div
          className={`w-2.5 h-2.5 rounded-full ${
            isCompleted ? "bg-emerald-500" : status === "failed" ? "bg-rose-500" : "bg-indigo-500 animate-pulse"
          }`}
        />
        <span className="text-sm text-slate-400 capitalize font-mono">
          {isCompleted
            ? "completed"
            : status === "synthesising"
            ? "writing conclusion"
            : status === "debating"
            ? `round ${currentRound} in progress`
            : status}
        </span>
      </div>

      {/* Timeline */}
      <DebateTimeline currentRound={currentRound} status={isCompleted ? "completed" : status} />

      {effectiveSynthesis?.conclusion && effectiveDistribution && (
        <ConclusionPanel
          conclusion={effectiveSynthesis.conclusion}
          weightedMean={effectiveDistribution.weighted_mean}
        />
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Agent Cards */}
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Agent Positions</h2>
          {latestPositions.length === 0 ? (
            <div className="rounded-xl border border-slate-800 p-8 text-center text-slate-600">
              Waiting for agents to form positions...
            </div>
          ) : (
            latestPositions.map((pos) => (
              <AgentCard key={`${pos.agent_id}-${pos.round_number}`} position={pos} />
            ))
          )}
        </div>

        {/* Belief Distribution — sticks while the taller card column scrolls */}
        <div className="space-y-3 lg:sticky lg:top-6 lg:self-start">
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Belief Distribution</h2>
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
            {effectiveDistribution ? (
              <BeliefDistributionChart distribution={effectiveDistribution} />
            ) : (
              <div className="h-48 flex items-center justify-center text-slate-600 text-sm">
                Distribution available after debate completes
              </div>
            )}
          </div>
        </div>
      </div>

      {/* How belief moved */}
      {effectiveSynthesis?.trajectory?.agents?.length ? (
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
            How Belief Moved
          </h2>
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
            <BeliefTrajectory trajectory={effectiveSynthesis.trajectory} />
          </div>
        </div>
      ) : null}

      {/* The back-and-forth itself */}
      {effectiveSynthesis?.exchanges?.length ? (
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
            Exchanges
            <span className="ml-2 text-slate-600 normal-case font-normal tracking-normal">
              who challenged whom
            </span>
          </h2>
          <Exchanges exchanges={effectiveSynthesis.exchanges} />
        </div>
      ) : null}

      {/* Argument Graph */}
      {effectiveGraph && effectiveGraph.nodes.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Argument Graph</h2>
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
            <ArgumentGraphViz graph={effectiveGraph} />
          </div>
        </div>
      )}

      {/* Unknown Unknowns */}
      {effectiveUnknowns.length > 0 && <UnknownUnknowns questions={effectiveUnknowns} />}
    </div>
  );
}
