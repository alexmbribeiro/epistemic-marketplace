from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.agent import CognitiveAgent
from app.models.debate import AgentPosition, Debate, JuryRating

router = APIRouter(prefix="/calibration", tags=["calibration"])


@router.get("/leaderboard")
async def leaderboard(db: AsyncSession = Depends(get_db)):
    """Elo from peer rating, with the per-criterion averages behind it."""
    agents = (
        await db.execute(select(CognitiveAgent).order_by(CognitiveAgent.elo_rating.desc()))
    ).scalars().all()

    breakdown = (
        await db.execute(
            select(
                JuryRating.subject_agent_id,
                func.avg(JuryRating.method_fidelity),
                func.avg(JuryRating.engagement),
                func.avg(JuryRating.crux_quality),
                func.avg(JuryRating.responsiveness),
                func.count(JuryRating.id),
            )
            .join(Debate, Debate.id == JuryRating.debate_id)
            .where(Debate.ranked)
            .group_by(JuryRating.subject_agent_id)
        )
    ).all()
    by_agent = {
        row[0]: {
            "method_fidelity": round(float(row[1]), 1),
            "engagement": round(float(row[2]), 1),
            "crux_quality": round(float(row[3]), 1),
            "responsiveness": round(float(row[4]), 1),
            "ratings_received": row[5],
        }
        for row in breakdown
    }

    return [
        {
            "agent_id": str(a.id),
            "name": a.name,
            "archetype": a.archetype,
            "description": a.description,
            "elo_rating": round(a.elo_rating, 1),
            "debates_rated_in": a.debates_rated_in,
            "debates_judged": a.debates_judged,
            # Provisional until it has been through a few debates — Elo on a
            # handful of results is mostly noise and should be read as such.
            "provisional": (a.debates_rated_in or 0) < 5,
            "criteria": by_agent.get(a.id),
        }
        for a in agents
    ]


@router.get("/judge-bias")
async def judge_bias(db: AsyncSession = Depends(get_db)):
    """Mean score each judge gives each subject.

    Philosophers judging philosophers carry their school with them. This does
    not remove that, it makes it visible: a judge that rates one opponent far
    below everyone else is showing its priors, not their craft.
    """
    rows = (
        await db.execute(
            select(
                JuryRating.judge_agent_id,
                JuryRating.subject_agent_id,
                func.avg(JuryRating.overall),
                func.count(JuryRating.id),
            )
            .join(Debate, Debate.id == JuryRating.debate_id)
            .where(Debate.ranked)
            .group_by(JuryRating.judge_agent_id, JuryRating.subject_agent_id)
        )
    ).all()
    names = {
        a.id: a.name for a in (await db.execute(select(CognitiveAgent))).scalars().all()
    }
    return [
        {
            "judge": names.get(r[0], "?"),
            "subject": names.get(r[1], "?"),
            "mean_score": round(float(r[2]), 1),
            "n": r[3],
        }
        for r in rows
    ]


@router.get("/fault-lines")
async def fault_lines(db: AsyncSession = Depends(get_db)):
    """The pairs that end up furthest apart, across every debate they shared.

    Not a per-agent statistic: this is where the roster actually splits. A
    pair that has only met once is noise, so each row carries its count and
    the caller decides what to trust.
    """
    finals = (
        await db.execute(
            select(AgentPosition.debate_id, AgentPosition.agent_id, AgentPosition.probability_true)
            .join(Debate, Debate.id == AgentPosition.debate_id)
            .where(AgentPosition.round_number == 3, Debate.ranked)
        )
    ).all()
    names = {a.id: a.name for a in (await db.execute(select(CognitiveAgent))).scalars().all()}

    by_debate: dict = {}
    for debate_id, agent_id, score in finals:
        by_debate.setdefault(debate_id, {})[agent_id] = score

    gaps: dict = {}
    for scores in by_debate.values():
        ids = sorted(scores, key=str)
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                gaps.setdefault((a, b), []).append(abs(scores[a] - scores[b]))

    rows = [
        {
            "a": names.get(a, "?"),
            "b": names.get(b, "?"),
            "mean_gap": round(sum(v) / len(v), 3),
            "n": len(v),
        }
        for (a, b), v in gaps.items()
    ]
    rows.sort(key=lambda r: -r["mean_gap"])
    return {"furthest_apart": rows[:5], "closest": sorted(rows, key=lambda r: r["mean_gap"])[:5]}
