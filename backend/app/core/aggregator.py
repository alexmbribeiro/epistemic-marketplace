import math

from app.agents.base_agent import AgentResult


def compute_belief_distribution(positions: list[AgentResult]) -> dict:
    """Aggregate the agents' final beliefs.

    There used to be a reputation weighting here. It was never anything:
    reputation_score was seeded at 1.0 and no code ever moved it, so every
    weight was log1p(1.0) and the weighted mean equalled the plain mean in
    every debate ever run. It is gone rather than left implying a weighting
    that does not happen. Peer Elo deliberately does not replace it — see
    core/jury.py on why the map of uncertainty is not weighted by how well
    rival schools rate you.
    """
    if not positions:
        return {"mean": 0.5, "std": 0.0, "buckets": [], "dominant_agents": []}

    beliefs = [pos.belief_score for pos in positions]
    mean = sum(beliefs) / len(beliefs)
    variance = sum((b - mean) ** 2 for b in beliefs) / len(beliefs)
    std = math.sqrt(variance)

    # Build belief buckets (0-0.2, 0.2-0.4, 0.4-0.6, 0.6-0.8, 0.8-1.0)
    bucket_labels = ["0.0–0.2", "0.2–0.4", "0.4–0.6", "0.6–0.8", "0.8–1.0"]
    bucket_counts = [0] * 5
    for b in beliefs:
        idx = min(int(b * 5), 4)
        bucket_counts[idx] += 1
    buckets = [{"range": label, "count": count, "pct": count / len(beliefs)} for label, count in zip(bucket_labels, bucket_counts)]

    # The agents furthest from the fence — the ones actually driving the spread.
    scored = sorted(positions, key=lambda p: abs(p.belief_score - 0.5), reverse=True)
    dominant = [{"agent_name": p.agent_name, "belief_score": p.belief_score} for p in scored[:3]]

    # Identify zone of disagreement
    zone = _identify_disagreement_zone(positions)

    return {
        "mean": round(mean, 4),
        "std": round(std, 4),
        "buckets": buckets,
        "dominant_agents": dominant,
        "disagreement_zone": zone,
        "agent_count": len(positions),
    }


def _identify_disagreement_zone(positions: list[AgentResult]) -> str:
    """Find the crux where agents disagree most."""
    all_cruxes = []
    for pos in positions:
        all_cruxes.extend(pos.cruxes)

    if not all_cruxes:
        return "No specific crux identified"

    # Return the first crux as the primary zone of disagreement
    # In a more sophisticated version, this would cluster cruxes semantically
    return all_cruxes[0] if all_cruxes else "Multiple competing frameworks"
