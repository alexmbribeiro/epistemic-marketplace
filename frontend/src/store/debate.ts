import { create } from "zustand";
import type { AgentPosition, AllPositions, BeliefDistribution, ArgumentGraph, DebateEvent, Synthesis } from "@/types";

interface DebateState {
  debateId: string | null;
  status: string;
  currentRound: number;
  positions: AllPositions;
  finalDistribution: BeliefDistribution | null;
  argumentGraph: ArgumentGraph | null;
  unknownUnknowns: string[];
  synthesis: Synthesis | null;
  setDebateId: (id: string) => void;
  handleEvent: (event: DebateEvent) => void;
  reset: () => void;
}

const emptyPositions: AllPositions = { round1: [], round2: [], round3: [] };

export const useDebateStore = create<DebateState>((set) => ({
  debateId: null,
  status: "idle",
  currentRound: 0,
  positions: emptyPositions,
  finalDistribution: null,
  argumentGraph: null,
  unknownUnknowns: [],
  synthesis: null,

  setDebateId: (id) => set({ debateId: id, status: "connecting" }),

  handleEvent: (event) => {
    switch (event.event) {
      case "debate_started":
        set({ status: "started" });
        break;
      case "synthesising":
        set({ status: "synthesising" });
        break;
      case "round_started":
        set({ status: "debating", currentRound: (event.data as { round: number }).round });
        break;
      case "round1_complete":
        set((s) => ({
          positions: { ...s.positions, round1: (event.data as { positions: AgentPosition[] }).positions },
        }));
        break;
      case "round2_complete":
        set((s) => ({
          positions: { ...s.positions, round2: (event.data as { positions: AgentPosition[] }).positions },
        }));
        break;
      case "round3_complete":
        set((s) => ({
          positions: { ...s.positions, round3: (event.data as { positions: AgentPosition[] }).positions },
        }));
        break;
      case "debate_complete": {
        const d = event.data as {
          final_belief_distribution: BeliefDistribution;
          argument_graph: ArgumentGraph;
          unknown_unknowns: string[];
          synthesis: Synthesis | null;
        };
        set({
          status: "completed",
          finalDistribution: d.final_belief_distribution,
          argumentGraph: d.argument_graph,
          unknownUnknowns: d.unknown_unknowns,
          synthesis: d.synthesis ?? null,
        });
        break;
      }
    }
  },

  reset: () =>
    set({
      debateId: null,
      status: "idle",
      currentRound: 0,
      positions: emptyPositions,
      finalDistribution: null,
      argumentGraph: null,
      unknownUnknowns: [],
      synthesis: null,
    }),
}));
