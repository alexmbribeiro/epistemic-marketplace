"""Derive the shape of a debate from its rounds.

The debate already produced a number. These turn the rounds into the things
a number cannot say: who moved, who dug in, who argued with whom, and whether
the agents ended up closer together or further apart.
"""

import statistics

from app.agents.base_agent import AgentResult


def build_trajectory(all_rounds: list[list[AgentResult]]) -> dict:
    """Per-agent belief across rounds, plus whether the group converged."""
    by_agent: dict[str, dict] = {}

    for positions in all_rounds:
        for pos in positions:
            entry = by_agent.setdefault(
                pos.agent_id,
                {
                    "agent_id": pos.agent_id,
                    "agent_name": pos.agent_name,
                    "archetype": pos.archetype,
                    "beliefs": [],
                },
            )
            entry["beliefs"].append(round(pos.belief_score, 4))

    agents = list(by_agent.values())
    for a in agents:
        b = a["beliefs"]
        deltas = [round(b[i + 1] - b[i], 4) for i in range(len(b) - 1)]
        # Net shift hides the interesting case. An agent that goes 0.30 -> 0.80
        # -> 0.25 nets to -0.05 and looks anchored, when it in fact swung
        # further than anyone. Swing is the total distance travelled.
        a["shift"] = round(b[-1] - b[0], 4) if b else 0.0
        a["swing"] = round(sum(abs(d) for d in deltas), 4)
        a["moved"] = a["swing"] >= 0.05
        # Did it change direction — argue one way, then come back?
        # Both legs must be substantial. At a 5pt threshold every small wobble
        # counts as a reversal, which buries the agent that genuinely swung 40.
        a["reversed"] = any(
            deltas[i] * deltas[i + 1] < 0 and min(abs(deltas[i]), abs(deltas[i + 1])) >= 0.10
            for i in range(len(deltas) - 1)
        )

    # Spread per round: falling means the debate pulled agents together.
    spread = []
    for positions in all_rounds:
        scores = [p.belief_score for p in positions]
        spread.append(round(statistics.pstdev(scores), 4) if len(scores) > 1 else 0.0)

    converged = None
    if len(spread) >= 2:
        delta = spread[-1] - spread[0]
        converged = "converged" if delta < -0.02 else "diverged" if delta > 0.02 else "unchanged"

    movers = sorted(agents, key=lambda a: a["swing"], reverse=True)

    return {
        "agents": agents,
        "spread_per_round": spread,
        "convergence": converged,
        "biggest_mover": movers[0] if movers and movers[0]["moved"] else None,
        "anchored": [a["agent_name"] for a in agents if not a["moved"]],
        "reversals": [a["agent_name"] for a in agents if a["reversed"]],
    }


def extract_exchanges(all_rounds: list[list[AgentResult]]) -> list[dict]:
    """Who challenged whom, in order. This is the back-and-forth itself."""
    exchanges = []
    for positions in all_rounds:
        for pos in positions:
            for ch in pos.challenges or []:
                target = (ch.get("target_agent") or "").strip()
                text = (ch.get("challenge") or "").strip()
                if not text:
                    continue
                exchanges.append(
                    {
                        "round": pos.round_number,
                        "from_agent": pos.agent_name,
                        "from_archetype": pos.archetype,
                        "to_agent": target or "the room",
                        "type": ch.get("type", "contradicts"),
                        "text": text,
                    }
                )
    return exchanges


def fallback_conclusion(distribution: dict, trajectory: dict) -> dict:
    """Used when the synthesis call fails. Says only what the numbers support."""
    mean = distribution.get("weighted_mean", 0.5)
    std = distribution.get("std", 0.0)

    if mean >= 0.65:
        lean = "leans true"
    elif mean <= 0.35:
        lean = "leans false"
    else:
        lean = "sits near even odds"

    if std >= 0.2:
        consensus = "deadlocked"
        agreement = "the agents did not agree"
    elif std >= 0.1:
        consensus = "contested"
        agreement = "the agents disagreed substantially"
    else:
        consensus = "leaning"
        agreement = "the agents broadly agreed"

    return {
        "verdict": f"After three rounds the claim {lean}, and {agreement}.",
        "reasoning": (
            f"Weighted belief settled at {mean:.0%} with a spread of {std:.0%}. "
            f"The group {trajectory.get('convergence') or 'did not measurably move'} "
            "over the course of the debate."
        ),
        "consensus": consensus,
        "what_would_settle_it": [distribution.get("disagreement_zone", "")] if distribution.get("disagreement_zone") else [],
        "generated": False,
    }
