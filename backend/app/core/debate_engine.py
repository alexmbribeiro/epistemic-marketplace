import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

import redis.asyncio as aioredis

from app.agents import AgentResult, build_agent
from app.agents.base_agent import BaseAgent
from app.config import settings
from app.core.aggregator import compute_belief_distribution
from app.core.argument_graph import build_argument_graph, extract_unknown_unknowns
from app.core.synthesis import build_trajectory, extract_exchanges, fallback_conclusion
from app.services import llm_service


logger = logging.getLogger(__name__)


async def _get_redis() -> aioredis.Redis:
    return await aioredis.from_url(settings.redis_url, decode_responses=True)


async def broadcast(debate_id: str, event: str, data: dict) -> None:
    redis = await _get_redis()
    try:
        payload = json.dumps({"event": event, "data": data})
        await redis.publish(f"debate:{debate_id}", payload)
    finally:
        await redis.aclose()


def _result_to_dict(result: AgentResult) -> dict:
    return {
        "agent_id": result.agent_id,
        "agent_name": result.agent_name,
        "archetype": result.archetype,
        "round_number": result.round_number,
        "belief_score": result.belief_score,
        "confidence_low": result.confidence_low,
        "confidence_high": result.confidence_high,
        "reasoning": result.reasoning,
        "key_evidence": result.key_evidence,
        "cruxes": result.cruxes,
        "argument_type": result.argument_type,
        "argument_content": result.argument_content,
        "argument_strength": result.argument_strength,
        "unanswered_questions": result.unanswered_questions,
        "challenges": result.challenges,
        "synthesis_notes": result.synthesis_notes,
    }


async def run_debate(
    debate_id: str,
    claim_content: str,
    agents: list[BaseAgent],
    reputation_map: dict[str, float],
    on_update=None,
) -> dict:
    """
    Orchestrate a full 3-round debate.
    on_update: optional async callback(debate_id, event, data) for WebSocket broadcasting
    """

    async def emit(event: str, data: dict):
        await broadcast(debate_id, event, data)
        if on_update:
            await on_update(debate_id, event, data)

    await emit("debate_started", {"debate_id": debate_id, "agent_count": len(agents)})

    # Round 1: Independent positions (fully parallel)
    await emit("round_started", {"round": 1})
    round1: list[AgentResult] = await asyncio.gather(*[
        agent.form_position(claim_content) for agent in agents
    ])
    await emit("round1_complete", {"positions": [_result_to_dict(r) for r in round1]})

    # Round 2: Cross-challenges (parallel, but each agent sees round1)
    await emit("round_started", {"round": 2})
    round2: list[AgentResult] = await asyncio.gather(*[
        agent.challenge(claim_content, list(round1)) for agent in agents
    ])
    await emit("round2_complete", {"positions": [_result_to_dict(r) for r in round2]})

    # Round 3: Synthesis
    await emit("round_started", {"round": 3})
    round3: list[AgentResult] = await asyncio.gather(*[
        agent.synthesize(claim_content, list(round1), list(round2)) for agent in agents
    ])
    await emit("round3_complete", {"positions": [_result_to_dict(r) for r in round3]})

    # Aggregate final distribution
    distribution = compute_belief_distribution(round3, reputation_map)

    # Build argument graph
    graph = build_argument_graph([list(round1), list(round2), list(round3)])

    # Unknown unknowns
    unknowns = extract_unknown_unknowns([list(round1), list(round2), list(round3)])

    # How belief actually moved, and who argued with whom
    rounds = [list(round1), list(round2), list(round3)]
    trajectory = build_trajectory(rounds)
    exchanges = extract_exchanges(rounds)

    await emit("synthesising", {"debate_id": debate_id})
    try:
        conclusion = await llm_service.synthesize_conclusion(
            claim_content, list(round3), distribution, trajectory
        )
    except Exception:
        # A debate that produced three full rounds must not be thrown away
        # because the closing summary failed.
        logger.warning("Conclusion synthesis failed; using computed fallback", exc_info=True)
        conclusion = fallback_conclusion(distribution, trajectory)

    synthesis = {
        "conclusion": conclusion,
        "trajectory": trajectory,
        "exchanges": exchanges,
        # The agent_positions table stores no archetype, argument_type or
        # argument_content, so a completed debate loaded fresh had nothing to
        # render its cards from. Keep the full rounds here.
        "positions": {
            "round1": [_result_to_dict(r) for r in round1],
            "round2": [_result_to_dict(r) for r in round2],
            "round3": [_result_to_dict(r) for r in round3],
        },
    }

    result = {
        "debate_id": debate_id,
        "final_belief_distribution": distribution,
        "argument_graph": graph,
        "unknown_unknowns": unknowns,
        "synthesis": synthesis,
        "all_positions": {
            "round1": [_result_to_dict(r) for r in round1],
            "round2": [_result_to_dict(r) for r in round2],
            "round3": [_result_to_dict(r) for r in round3],
        },
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }

    await emit("debate_complete", result)
    return result
