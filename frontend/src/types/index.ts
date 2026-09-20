export type ArchetypeId =
  | "bayesian"
  | "falsificationist"
  | "analogist"
  | "contrarian"
  | "dialectician"
  | "frequentist"
  | "domain_expert"
  | "custom";

export interface Claim {
  id: string;
  content: string;
  category: string;
  status: "pending" | "debating" | "resolved" | "expired";
  is_verifiable: boolean;
  created_at: string;
}

export interface CognitiveAgent {
  id: string;
  name: string;
  archetype: ArchetypeId;
  description: string;
  config: Record<string, unknown>;
  is_public: boolean;
  reputation_score: number;
  creator_id: string | null;
  created_at: string;
}

export interface AgentPosition {
  agent_id: string;
  agent_name: string;
  archetype: ArchetypeId;
  round_number: number;
  belief_score: number;
  confidence_low: number;
  confidence_high: number;
  reasoning: string;
  key_evidence: string[];
  cruxes: string[];
  argument_type: "supports" | "contradicts" | "qualifies" | "redefines" | "uncertain";
  argument_content: string;
  argument_strength: number;
  unanswered_questions: string[];
  challenges: Challenge[];
  synthesis_notes: string;
}

export interface Challenge {
  target_agent: string;
  challenge: string;
  type: "contradicts" | "qualifies" | "redefines";
}

export interface BeliefDistribution {
  mean: number;
  weighted_mean: number;
  std: number;
  buckets: BeliefBucket[];
  dominant_agents: DominantAgent[];
  disagreement_zone: string;
  agent_count: number;
}

export interface BeliefBucket {
  range: string;
  count: number;
  pct: number;
}

export interface DominantAgent {
  agent_name: string;
  belief_score: number;
  weight: number;
}

export interface ArgumentNode {
  id: string;
  label: string;
  type: "claim" | "position";
  archetype?: ArchetypeId;
  belief_score?: number;
  argument_content?: string;
  round?: number;
  group: number;
}

export interface ArgumentEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  strength: number;
  label: string;
  challenge_text?: string;
}

export interface ArgumentGraph {
  nodes: ArgumentNode[];
  edges: ArgumentEdge[];
}

export interface Debate {
  id: string;
  claim_id: string;
  status: "initializing" | "round1" | "round2" | "round3" | "completed" | "failed";
  agent_ids: string[];
  final_belief_distribution: BeliefDistribution | null;
  argument_graph: ArgumentGraph | null;
  unknown_unknowns: string[] | null;
  created_at: string;
  completed_at: string | null;
}

export interface DebateEvent {
  event:
    | "debate_started"
    | "round_started"
    | "round1_complete"
    | "round2_complete"
    | "round3_complete"
    | "debate_complete";
  data: Record<string, unknown>;
}

export interface AllPositions {
  round1: AgentPosition[];
  round2: AgentPosition[];
  round3: AgentPosition[];
}
