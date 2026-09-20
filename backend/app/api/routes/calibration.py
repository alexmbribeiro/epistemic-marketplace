from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.agent import CalibrationRecord, CognitiveAgent

router = APIRouter(prefix="/calibration", tags=["calibration"])


@router.get("/leaderboard")
async def leaderboard(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CognitiveAgent).order_by(CognitiveAgent.reputation_score.desc()).limit(20)
    )
    agents = result.scalars().all()
    return [
        {
            "agent_id": str(a.id),
            "name": a.name,
            "archetype": a.archetype,
            "reputation_score": a.reputation_score,
            "description": a.description,
        }
        for a in agents
    ]
