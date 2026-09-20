import math

from app.agents.base_agent import AgentResult


def lmsr_weight(reputation: float) -> float:
    """Convert reputation score to LMSR market weight."""
    return math.log1p(reputation)


def compute_belief_distribution(positions: list[AgentResult], reputation_map: dict[str, float]) -> dict:
    """
    Aggregate agent beliefs using weighted average (LMSR-inspired).
    reputation_map: {agent_id: reputation_score}
    """
    if not positions:
        return {"mean": 0.5, "std": 0.0, "weighted_mean": 0.5, "buckets": [], "dominant_agents": []}

    weights = []
    beliefs = []
    for pos in positions:
        rep = reputation_map.get(pos.agent_id, 1.0)
        w = lmsr_weight(rep)
        weights.append(w)
        beliefs.append(pos.belief_score)

    total_weight = sum(weights)
    weighted_mean = sum(b * w for b, w in zip(beliefs, weights)) / total_weight

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

    # Find dominant agents (highest weighted belief contributors)
    scored = sorted(
        zip(positions, weights),
        key=lambda x: abs(x[0].belief_score - 0.5) * x[1],
        reverse=True,
    )
    dominant = [{"agent_name": p.agent_name, "belief_score": p.belief_score, "weight": w} for p, w in scored[:3]]

    # Identify zone of disagreement
    zone = _identify_disagreement_zone(positions)

    return {
        "mean": round(mean, 4),
        "weighted_mean": round(weighted_mean, 4),
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
