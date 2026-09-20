import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_user
from app.database import get_db
from app.models.agent import CognitiveAgent
from app.models.user import User
from app.schemas.agent import AgentCreate, AgentResponse

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/", response_model=list[AgentResponse])
async def list_agents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CognitiveAgent).where(CognitiveAgent.is_public == True).order_by(CognitiveAgent.reputation_score.desc())
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
