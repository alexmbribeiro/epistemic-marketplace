import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_user
from app.database import get_db
from app.models.agent import CognitiveAgent
from app.models.claim import Claim
from app.models.debate import AgentPosition, Debate, JuryRating
from app.models.user import User
from app.schemas.agent import AgentCreate, AgentResponse

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/", response_model=list[AgentResponse])
async def list_agents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CognitiveAgent).where(CognitiveAgent.is_public == True).order_by(CognitiveAgent.elo_rating.desc())
    )
    return result.scalars().all()


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CognitiveAgent).where(CognitiveAgent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.post("/", response_model=AgentResponse, status_code=201)
async def create_agent(
    body: AgentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    agent = CognitiveAgent(
        name=body.name,
        archetype=body.archetype,
        system_prompt=body.system_prompt,
        description=body.description,
        config=body.config,
        is_public=body.is_public,
        creator_id=current_user.id,
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


def _pair(rows, label_a, label_b, n=2):
    ranked = sorted(rows, key=lambda r: r["value"])
    return {label_a: ranked[-n:][::-1], label_b: ranked[:n]}


@router.get("/{agent_id}/stats")
async def agent_stats(agent_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Who this agent lines up with, who scores it well, and how it behaves.

    All of it is derived from what debates already record — no extra model
    calls. Everything is thin at low debate counts, so each block reports the
    sample it rests on rather than presenting a single number as settled.
    """
    agent = (await db.execute(select(CognitiveAgent).where(CognitiveAgent.id == agent_id))).scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    names = {a.id: a.name for a in (await db.execute(select(CognitiveAgent))).scalars().all()}

    # Final-round belief per agent per debate.
    finals = (
        await db.execute(
            select(AgentPosition.debate_id, AgentPosition.agent_id, AgentPosition.probability_true)
            .join(Debate, Debate.id == AgentPosition.debate_id)
            .where(AgentPosition.round_number == 3, Debate.ranked)
        )
    ).all()

    by_debate: dict = {}
    for debate_id, aid, score in finals:
        by_debate.setdefault(debate_id, {})[aid] = score

    # Agreement: mean gap in final belief across debates actually shared.
    gaps: dict = {}
    own_scores, distances = [], []
    for debate_id, scores in by_debate.items():
        if agent_id not in scores:
            continue
        mine = scores[agent_id]
        own_scores.append(mine)
        others = [v for k, v in scores.items() if k != agent_id]
        if others:
            distances.append(abs(mine - sum(others) / len(others)))
        for other_id, theirs in scores.items():
            if other_id == agent_id:
                continue
            gaps.setdefault(other_id, []).append(abs(mine - theirs))

    agreement = [
        {"name": names.get(k, "?"), "value": round(sum(v) / len(v), 3), "n": len(v)}
        for k, v in gaps.items()
    ]
    # Lower gap = closer, so the labels invert the sort.
    closest = sorted(agreement, key=lambda r: r["value"])[:2]
    furthest = sorted(agreement, key=lambda r: -r["value"])[:2]

    # As judge, and as subject.
    given = (
        await db.execute(
            select(JuryRating.subject_agent_id, func.avg(JuryRating.overall), func.count(JuryRating.id))
            .join(Debate, Debate.id == JuryRating.debate_id)
            .where(JuryRating.judge_agent_id == agent_id, Debate.ranked)
            .group_by(JuryRating.subject_agent_id)
        )
    ).all()
    received = (
        await db.execute(
            select(JuryRating.judge_agent_id, func.avg(JuryRating.overall), func.count(JuryRating.id))
            .join(Debate, Debate.id == JuryRating.debate_id)
            .where(JuryRating.subject_agent_id == agent_id, Debate.ranked)
            .group_by(JuryRating.judge_agent_id)
        )
    ).all()
    fmt = lambda rows: [
        {"name": names.get(r[0], "?"), "value": round(float(r[1]), 1), "n": r[2]} for r in rows
    ]

    own_criteria = (
        await db.execute(
            select(
                func.avg(JuryRating.method_fidelity),
                func.avg(JuryRating.engagement),
                func.avg(JuryRating.crux_quality),
                func.avg(JuryRating.responsiveness),
                func.count(JuryRating.id),
            )
            .join(Debate, Debate.id == JuryRating.debate_id)
            .where(JuryRating.subject_agent_id == agent_id, Debate.ranked)
        )
    ).first()

    # Swing: total distance travelled across rounds, averaged over debates.
    all_positions = (
        await db.execute(
            select(AgentPosition.debate_id, AgentPosition.round_number, AgentPosition.probability_true)
            .join(Debate, Debate.id == AgentPosition.debate_id)
            .where(AgentPosition.agent_id == agent_id, Debate.ranked)
            .order_by(AgentPosition.debate_id, AgentPosition.round_number)
        )
    ).all()
    per_debate: dict = {}
    for debate_id, rnd, score in all_positions:
        per_debate.setdefault(debate_id, []).append(score)
    swings = [
        sum(abs(v[i + 1] - v[i]) for i in range(len(v) - 1)) for v in per_debate.values() if len(v) > 1
    ]

    # --- Reciprocity -------------------------------------------------------
    # Whether A scores B the way B scores A. The asymmetry is the interesting
    # part and an average hides it by construction: two agents can both sit at
    # the mean while one consistently marks the other down.
    given_map = {r[0]: float(r[1]) for r in given}
    received_map = {r[0]: float(r[1]) for r in received}
    reciprocity = [
        {
            "name": names.get(other, "?"),
            "i_give": round(given_map[other], 1),
            "they_give": round(received_map[other], 1),
            "gap": round(given_map[other] - received_map[other], 1),
        }
        for other in set(given_map) & set(received_map)
    ]
    reciprocity.sort(key=lambda r: -abs(r["gap"]))

    # --- Craft by claim category -------------------------------------------
    # A Humean should do well on empirical claims and badly on metaphysical
    # ones. Whether that actually shows up is a test of the prompts.
    cats = (
        await db.execute(
            select(Claim.category, func.avg(JuryRating.overall), func.count(JuryRating.id))
            .join(Debate, Debate.claim_id == Claim.id)
            .join(JuryRating, JuryRating.debate_id == Debate.id)
            .where(JuryRating.subject_agent_id == agent_id, Debate.ranked)
            .group_by(Claim.category)
        )
    ).all()
    by_category = sorted(
        [{"name": c[0], "value": round(float(c[1]), 1), "n": c[2]} for c in cats],
        key=lambda r: -r["value"],
    )

    # --- Where the movement happens ----------------------------------------
    # Leg one is the response to seeing the room; leg two is the response to
    # being cross-examined. An agent that only moves on leg one drifts with
    # the company; one that moves on leg two is answering an argument.
    leg1 = [abs(v[1] - v[0]) for v in per_debate.values() if len(v) > 2]
    leg2 = [abs(v[2] - v[1]) for v in per_debate.values() if len(v) > 2]

    # --- Crux influence ----------------------------------------------------
    # NOT citation: nothing records whether anyone was actually moved by a
    # crux. This is how often this agent's cruxes were the best-rated in the
    # debate — peer judgement of the crux, not evidence it persuaded.
    per_debate_crux = (
        await db.execute(
            select(JuryRating.debate_id, JuryRating.subject_agent_id, func.avg(JuryRating.crux_quality))
            .join(Debate, Debate.id == JuryRating.debate_id)
            .where(Debate.ranked)
            .group_by(JuryRating.debate_id, JuryRating.subject_agent_id)
        )
    ).all()
    best_by_debate: dict = {}
    for debate_id, subject, avg_crux in per_debate_crux:
        cur = best_by_debate.get(debate_id)
        if cur is None or float(avg_crux) > cur[1]:
            best_by_debate[debate_id] = (subject, float(avg_crux))
    my_debates = {d for d, subj, _ in per_debate_crux if subj == agent_id}
    top_crux = sum(1 for d in my_debates if best_by_debate.get(d, (None,))[0] == agent_id)

    return {
        "agent_id": str(agent.id),
        "name": agent.name,
        "archetype": agent.archetype,
        "description": agent.description,
        "elo_rating": round(agent.elo_rating, 1),
        "debates": agent.debates_rated_in,
        "judged": agent.debates_judged,
        "provisional": (agent.debates_rated_in or 0) < 5,
        "criteria": (
            {
                "method_fidelity": round(float(own_criteria[0]), 1),
                "engagement": round(float(own_criteria[1]), 1),
                "crux_quality": round(float(own_criteria[2]), 1),
                "responsiveness": round(float(own_criteria[3]), 1),
                "n": own_criteria[4],
            }
            if own_criteria and own_criteria[4]
            else None
        ),
        "agrees_most_with": closest,
        "disagrees_most_with": furthest,
        "rates_highest": sorted(fmt(given), key=lambda r: -r["value"])[:2],
        "rates_lowest": sorted(fmt(given), key=lambda r: r["value"])[:2],
        "rated_best_by": sorted(fmt(received), key=lambda r: -r["value"])[:2],
        "rated_worst_by": sorted(fmt(received), key=lambda r: r["value"])[:2],
        "reciprocity": reciprocity[:3],
        "by_category": by_category,
        "movement": {
            # Mean absolute change on each leg, in belief points.
            "on_seeing_others": round(sum(leg1) / len(leg1), 3) if leg1 else None,
            "on_being_challenged": round(sum(leg2) / len(leg2), 3) if leg2 else None,
            "n": len(leg1),
        },
        "crux_influence": {
            "top_in_debates": top_crux,
            "of_debates": len(my_debates),
        },
        "disposition": {
            # Above 0.5 this agent tends to affirm; below, to doubt.
            "mean_belief": round(sum(own_scores) / len(own_scores), 3) if own_scores else None,
            # How far it habitually sits from the rest of the room.
            "mean_distance_from_room": round(sum(distances) / len(distances), 3) if distances else None,
            # How much ground it covers across three rounds.
            "mean_swing": round(sum(swings) / len(swings), 3) if swings else None,
            "n": len(own_scores),
        },
    }
