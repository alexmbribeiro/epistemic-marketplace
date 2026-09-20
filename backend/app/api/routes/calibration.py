from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.agent import CognitiveAgent
from app.models.debate import JuryRating

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
            ).group_by(JuryRating.subject_agent_id)
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
            ).group_by(JuryRating.judge_agent_id, JuryRating.subject_agent_id)
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
