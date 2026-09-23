/**
 * The seeded archetypes, plus any string — a user-authored agent can carry an
 * archetype nobody has seen before, so a closed union here would be a lie.
 * The `(string & {})` arm keeps autocomplete for the known ones.
 */
export type ArchetypeId =
  | "bayesian"
  | "falsificationist"
  | "analogist"
  | "contrarian"
  | "dialectician"
  | "frequentist"
  | "domain_expert"
  | "nietzschean"
  | "jungian"
  | "aristotelian"
  | "humean"
  | "kantian"
  | "wittgensteinian"
  | "pragmatist"
  | "adlerian"
  | "custom"
  // eslint-disable-next-line @typescript-eslint/ban-types
  | (string & {});

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
  elo_rating: number;
  debates_rated_in: number;
  debates_judged: number;
  creator_id: string | null;
  created_at: string;
}

export interface AgentPosition {
  agent_id: string;
  agent_name: string;
  archetype: ArchetypeId;
  round_number: number;
  /** The agent's own verdict, in whatever its method measures. */
  belief_score: number;
  /** Probability the claim is literally true, on the scale every agent shares.
   *  This is the one that gets averaged, charted and compared. */
  probability_true: number;
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

export interface TrajectoryAgent {
  agent_id: string;
  agent_name: string;
  archetype: ArchetypeId;
  beliefs: number[];
  /** Net change, first round to last. */
  shift: number;
  /** Total distance travelled across rounds — catches an agent that moved and came back. */
  /** Absent on debates recorded before this metric existed. */
  swing?: number;
  moved: boolean;
  reversed: boolean;
}

export interface Trajectory {
  agents: TrajectoryAgent[];
  spread_per_round: number[];
  convergence: "converged" | "diverged" | "unchanged" | null;
  biggest_mover: TrajectoryAgent | null;
  anchored: string[];
  reversals: string[];
}

export interface Exchange {
  round: number;
  from_agent: string;
  from_archetype: ArchetypeId;
  to_agent: string;
  type: "contradicts" | "qualifies" | "redefines";
  text: string;
}

export interface Conclusion {
  verdict: string;
  reasoning: string;
  consensus: "strong_agreement" | "leaning" | "contested" | "deadlocked";
  what_would_settle_it: string[];
  generated: boolean;
}

export interface Synthesis {
  conclusion: Conclusion;
  trajectory: Trajectory;
  exchanges: Exchange[];
  positions?: AllPositions;
}

export interface Debate {
  id: string;
  claim_id: string;
  claim_content: string | null;
  claim_category: string | null;
  status: "initializing" | "round1" | "round2" | "round3" | "completed" | "failed";
  agent_ids: string[];
  final_belief_distribution: BeliefDistribution | null;
  argument_graph: ArgumentGraph | null;
  unknown_unknowns: string[] | null;
  synthesis: Synthesis | null;
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
    | "synthesising"
    | "debate_complete";
  data: Record<string, unknown>;
}

export interface AllPositions {
  round1: AgentPosition[];
  round2: AgentPosition[];
  round3: AgentPosition[];
}


export interface LeaderboardEntry {
  agent_id: string;
  name: string;
  archetype: ArchetypeId;
  description: string;
  elo_rating: number;
  debates_rated_in: number;
  debates_judged: number;
  /** Under five rated debates the number is mostly noise. */
  provisional: boolean;
  criteria: {
    method_fidelity: number;
    engagement: number;
    crux_quality: number;
    responsiveness: number;
    ratings_received: number;
  } | null;
}

export interface JudgeBiasRow {
  judge: string;
  subject: string;
  mean_score: number;
  n: number;
}


/** One side of a comparison: another agent, a number, and the sample it rests on. */
export interface StatRow {
  name: string;
  value: number;
  n: number;
}

export interface AgentStats {
  agent_id: string;
  name: string;
  archetype: ArchetypeId;
  description: string;
  elo_rating: number;
  debates: number;
  judged: number;
  provisional: boolean;
  criteria: {
    method_fidelity: number;
    engagement: number;
    crux_quality: number;
    responsiveness: number;
    n: number;
  } | null;
  agrees_most_with: StatRow[];
  disagrees_most_with: StatRow[];
  rates_highest: StatRow[];
  rates_lowest: StatRow[];
  rated_best_by: StatRow[];
  rated_worst_by: StatRow[];
  reciprocity: { name: string; i_give: number; they_give: number; gap: number }[];
  by_category: StatRow[];
  movement: {
    on_seeing_others: number | null;
    on_being_challenged: number | null;
    n: number;
  };
  crux_influence: { top_in_debates: number; of_debates: number };
  disposition: {
    mean_belief: number | null;
    mean_distance_from_room: number | null;
    mean_swing: number | null;
    n: number;
  };
}

export interface FaultLine {
  a: string;
  b: string;
  mean_gap: number;
  n: number;
}

export interface FaultLines {
  furthest_apart: FaultLine[];
  closest: FaultLine[];
}
