import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import DEFAULT_ARCHETYPES, build_agent
from app.api.deps import get_current_user
from app.config import settings
from app.core.debate_engine import run_debate
from app.database import AsyncSessionLocal, get_db
from app.models.agent import CognitiveAgent
from app.models.claim import Claim
from app.models.debate import AgentPosition, Argument, Debate
from app.models.user import User
from app.schemas.debate import DebateCreate, DebateResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/debates", tags=["debates"])


@router.post("/", response_model=DebateResponse, status_code=201)
async def create_debate(
    body: DebateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    claim_result = await db.execute(select(Claim).where(Claim.id == body.claim_id))
    claim = claim_result.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    # Resolve which agents to use
    archetypes = body.agent_archetypes or DEFAULT_ARCHETYPES
    agent_db_records = []
    for archetype in archetypes:
        result = await db.execute(
            select(CognitiveAgent).where(CognitiveAgent.archetype == archetype, CognitiveAgent.creator_id == None)
        )
        rec = result.scalar_one_or_none()
        if rec:
            agent_db_records.append(rec)

    if not agent_db_records:
        raise HTTPException(status_code=400, detail="No agents available for selected archetypes")

    agent_ids = [rec.id for rec in agent_db_records]
    debate = Debate(
        claim_id=claim.id,
        status="initializing",
        agent_ids=agent_ids,
    )
    db.add(debate)
    await db.commit()
    await db.refresh(debate)

    # Update claim status
    claim.status = "debating"
    await db.commit()

    # Run debate in background
    asyncio.create_task(_run_debate_background(str(debate.id), str(claim.id), claim.content, agent_db_records))

    return debate


async def _run_debate_background(debate_id: str, claim_id: str, claim_content: str, agent_records: list):
    async with AsyncSessionLocal() as db:
        try:
            # Build agent instances
            agents = [build_agent(rec.archetype, str(rec.id), rec.config) for rec in agent_records]
            reputation_map = {str(rec.id): rec.reputation_score for rec in agent_records}

            # Update status to round1
            debate_result_db = await db.execute(select(Debate).where(Debate.id == uuid.UUID(debate_id)))
            debate = debate_result_db.scalar_one()
            debate.status = "round1"
            await db.commit()

            result = await run_debate(debate_id, claim_content, agents, reputation_map)

            # Persist results
            debate_result_db = await db.execute(select(Debate).where(Debate.id == uuid.UUID(debate_id)))
            debate = debate_result_db.scalar_one()
            debate.status = "completed"
            debate.final_belief_distribution = result["final_belief_distribution"]
            debate.argument_graph = result["argument_graph"]
            debate.unknown_unknowns = result["unknown_unknowns"]
            debate.completed_at = datetime.now(timezone.utc)

            # Persist agent positions from all rounds
            all_positions = result["all_positions"]
            for round_key, positions in all_positions.items():
                for pos in positions:
                    db.add(AgentPosition(
                        debate_id=uuid.UUID(debate_id),
                        round_number=pos["round_number"],
                        agent_id=uuid.UUID(pos["agent_id"]),
                        belief_score=pos["belief_score"],
                        confidence_low=pos["confidence_low"],
                        confidence_high=pos["confidence_high"],
                        reasoning=pos["reasoning"],
                        key_evidence=pos["key_evidence"],
                        cruxes=pos["cruxes"],
                    ))

            # Update claim status
            claim_result = await db.execute(select(Claim).where(Claim.id == uuid.UUID(claim_id)))
            claim = claim_result.scalar_one()
            claim.status = "resolved"

            await db.commit()

        except Exception:
            logger.exception("Debate %s failed", debate_id)
            await db.rollback()
            debate_result_db = await db.execute(select(Debate).where(Debate.id == uuid.UUID(debate_id)))
            debate = debate_result_db.scalar_one_or_none()
            if debate:
                debate.status = "failed"
                await db.commit()


@router.get("/", response_model=list[DebateResponse])
async def list_debates(db: AsyncSession = Depends(get_db), limit: int = 20, offset: int = 0):
    result = await db.execute(select(Debate).order_by(Debate.created_at.desc()).limit(limit).offset(offset))
    return result.scalars().all()


@router.get("/{debate_id}", response_model=DebateResponse)
async def get_debate(debate_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Debate).where(Debate.id == debate_id))
    debate = result.scalar_one_or_none()
    if not debate:
        raise HTTPException(status_code=404, detail="Debate not found")
    return debate


@router.websocket("/{debate_id}/live")
async def debate_websocket(websocket: WebSocket, debate_id: str):
    await websocket.accept()
    redis = await aioredis.from_url(settings.redis_url, decode_responses=True)
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"debate:{debate_id}")

    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            await websocket.send_text(message["data"])
            # Close cleanly once the debate is over instead of leaving the
            # socket open forever on a channel that will never speak again.
            try:
                if json.loads(message["data"]).get("event") == "debate_complete":
                    break
            except (ValueError, AttributeError):
                pass
    except WebSocketDisconnect:
        pass
    except Exception:
        # A client that goes away mid-send raises from send_text, not on
        # receive, so WebSocketDisconnect alone does not cover it.
        logger.info("Websocket for debate %s ended", debate_id, exc_info=True)
    finally:
        await pubsub.unsubscribe(f"debate:{debate_id}")
        await redis.aclose()
        try:
            await websocket.close()
        except Exception:
            pass
