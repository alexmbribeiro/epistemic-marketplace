import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents import DEFAULT_ARCHETYPES, JURY_SIZE, build_agent
from app.core.jury import compute_elo_updates, select_jury
from app.api.deps import get_current_user
from app.config import settings
from app.agents.base_agent import AgentResult
from app.core.debate_engine import run_debate, run_jury
from app.database import AsyncSessionLocal, get_db
from app.models.agent import CognitiveAgent
from app.models.claim import Claim
from app.models.debate import AgentPosition, Argument, Debate, JuryRating
from app.models.user import User
from app.schemas.debate import DebateCreate, DebateResponse

logger = logging.getLogger(__name__)

MAX_AGENTS_PER_DEBATE = 8

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
    if body.agent_ids:
        result = await db.execute(select(CognitiveAgent).where(CognitiveAgent.id.in_(body.agent_ids)))
        found = {rec.id: rec for rec in result.scalars().all()}
        missing = [str(i) for i in body.agent_ids if i not in found]
        if missing:
            raise HTTPException(status_code=404, detail=f"Unknown agent(s): {', '.join(missing)}")
        # Preserve the order the caller asked for.
        agent_db_records = [found[i] for i in body.agent_ids]
        for rec in agent_db_records:
            if not rec.is_public and (current_user is None or rec.creator_id != current_user.id):
                raise HTTPException(status_code=403, detail=f"Agent '{rec.name}' is private")
    else:
        archetypes = body.agent_archetypes or DEFAULT_ARCHETYPES
        agent_db_records = []
        for archetype in archetypes:
            result = await db.execute(
                select(CognitiveAgent).where(CognitiveAgent.archetype == archetype, CognitiveAgent.creator_id == None)
            )
            rec = result.scalar_one_or_none()
            if rec:
                agent_db_records.append(rec)

    if len(agent_db_records) < 2:
        raise HTTPException(
            status_code=400,
            detail="A debate needs at least two agents — one agent cannot disagree with itself",
        )
    # Bounded by the categorical palette: past eight series a chart has no
    # validated colour left to give, and the rounds cost proportionally more.
    if len(agent_db_records) > MAX_AGENTS_PER_DEBATE:
        raise HTTPException(
            status_code=400,
            detail=f"A debate takes at most {MAX_AGENTS_PER_DEBATE} agents; {len(agent_db_records)} were selected",
        )

    # Judges are philosophers who did not take part. With eight on the roster
    # and five debating there is exactly one possible jury, so the sampling
    # only bites for smaller debates.
    all_agents = (await db.execute(select(CognitiveAgent).where(CognitiveAgent.creator_id == None))).scalars().all()
    participant_ids = {rec.id for rec in agent_db_records}
    jury_records = select_jury([a for a in all_agents], list(participant_ids), JURY_SIZE)

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
    asyncio.create_task(
        _run_debate_background(str(debate.id), str(claim.id), claim.content, agent_db_records, jury_records)
    )

    return debate


async def _run_debate_background(
    debate_id: str, claim_id: str, claim_content: str, agent_records: list, jury_records: list | None = None
):
    async with AsyncSessionLocal() as db:
        try:
            # Build agent instances
            agents = [
                build_agent(rec.archetype, str(rec.id), rec.config, rec.system_prompt, rec.name)
                for rec in agent_records
            ]
            jury = [
                build_agent(rec.archetype, str(rec.id), rec.config, rec.system_prompt, rec.name)
                for rec in (jury_records or [])
            ]

            # Update status to round1
            debate_result_db = await db.execute(select(Debate).where(Debate.id == uuid.UUID(debate_id)))
            debate = debate_result_db.scalar_one()
            debate.status = "round1"
            await db.commit()

            result = await run_debate(debate_id, claim_content, agents, jury=jury)

            # Persist results
            debate_result_db = await db.execute(select(Debate).where(Debate.id == uuid.UUID(debate_id)))
            debate = debate_result_db.scalar_one()
            debate.status = "completed"
            debate.final_belief_distribution = result["final_belief_distribution"]
            debate.argument_graph = result["argument_graph"]
            debate.unknown_unknowns = result["unknown_unknowns"]
            debate.synthesis = result.get("synthesis")
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

            await _record_jury(db, debate_id, result, agent_records, jury_records or [])

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


async def _record_jury(db, debate_id: str, result: dict, agent_records: list, jury_records: list) -> None:
    """Persist each judge's scores, then move the Elo of everyone who debated."""
    verdict = (result.get("synthesis") or {}).get("jury") or {}
    rows = verdict.get("rows") or []
    if not rows:
        return

    by_name = {rec.name: rec for rec in agent_records}
    judges_by_id = {str(rec.id): rec for rec in jury_records}

    for r in rows:
        subject = by_name.get(r["agent_name"])
        judge = judges_by_id.get(str(r.get("judge_agent_id")))
        if not subject or not judge:
            continue
        crit = [r["method_fidelity"], r["engagement"], r["crux_quality"], r["responsiveness"]]
        db.add(JuryRating(
            debate_id=uuid.UUID(debate_id),
            judge_agent_id=judge.id,
            subject_agent_id=subject.id,
            method_fidelity=r["method_fidelity"],
            engagement=r["engagement"],
            crux_quality=r["crux_quality"],
            responsiveness=r["responsiveness"],
            overall=sum(crit) / len(crit),
            comment=r.get("comment", ""),
        ))

    scores = verdict.get("scores") or {}
    mean_scores = {name: data["overall"] for name, data in scores.items() if name in by_name}
    if len(mean_scores) < 2:
        return

    # agent_records and jury_records were loaded in the request's session and
    # are detached from this one, so writing to them would be silently lost.
    # Re-read the rows this session owns before touching the Elo.
    wanted = [by_name[n].id for n in mean_scores] + [rec.id for rec in jury_records]
    live = {
        a.id: a
        for a in (await db.execute(select(CognitiveAgent).where(CognitiveAgent.id.in_(wanted)))).scalars().all()
    }

    current = {name: live[by_name[name].id].elo_rating for name in mean_scores}
    updated = compute_elo_updates(current, mean_scores)
    for name, new_elo in updated.items():
        agent = live[by_name[name].id]
        agent.elo_rating = new_elo
        agent.debates_rated_in = (agent.debates_rated_in or 0) + 1
    for rec in jury_records:
        judge = live.get(rec.id)
        if judge:
            judge.debates_judged = (judge.debates_judged or 0) + 1


@router.post("/{debate_id}/rejudge")
async def rejudge(debate_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Re-run the jury on a debate that already happened.

    A jury can die without taking the debate with it — the rounds are already
    persisted, so there is no reason to spend another twenty-one calls
    re-arguing a claim just because three judges hit a quota wall. This
    repairs the rating and the Elo from the stored transcript.
    """
    debate = (await db.execute(select(Debate).where(Debate.id == debate_id))).scalar_one_or_none()
    if not debate:
        raise HTTPException(status_code=404, detail="Debate not found")
    stored = (debate.synthesis or {}).get("positions")
    if not stored:
        raise HTTPException(status_code=400, detail="This debate stored no positions to judge")

    existing = (
        await db.execute(select(func.count(JuryRating.id)).where(JuryRating.debate_id == debate_id))
    ).scalar_one()
    if existing:
        raise HTTPException(
            status_code=409, detail=f"Already judged ({existing} ratings). Delete them first to redo."
        )

    rounds = [[AgentResult(**p) for p in stored[f"round{i}"]] for i in (1, 2, 3)]
    participant_ids = [uuid.UUID(p.agent_id) for p in rounds[0]]

    agent_records = list(
        (await db.execute(select(CognitiveAgent).where(CognitiveAgent.id.in_(participant_ids)))).scalars().all()
    )
    all_agents = (
        await db.execute(select(CognitiveAgent).where(CognitiveAgent.creator_id == None))
    ).scalars().all()
    jury_records = select_jury(list(all_agents), participant_ids, JURY_SIZE)
    jury = [
        build_agent(r.archetype, str(r.id), r.config, r.system_prompt, r.name) for r in jury_records
    ]

    claim = (await db.execute(select(Claim).where(Claim.id == debate.claim_id))).scalar_one()
    verdict = await run_jury(claim.content, rounds, jury)

    # JSONB does not notice in-place mutation; reassign so it is written.
    debate.synthesis = {**debate.synthesis, "jury": verdict}
    await _record_jury(db, str(debate_id), {"synthesis": debate.synthesis}, agent_records, jury_records)
    await db.commit()

    return {
        "debate_id": str(debate_id),
        "judges": [j["name"] for j in verdict.get("judges", [])],
        "ratings": len(verdict.get("rows", [])),
    }


@router.get("/", response_model=list[DebateResponse])
async def list_debates(db: AsyncSession = Depends(get_db), limit: int = 20, offset: int = 0):
    result = await db.execute(
        select(Debate)
        .options(selectinload(Debate.claim))
        .order_by(Debate.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()


@router.get("/{debate_id}", response_model=DebateResponse)
async def get_debate(debate_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Debate).options(selectinload(Debate.claim)).where(Debate.id == debate_id)
    )
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
