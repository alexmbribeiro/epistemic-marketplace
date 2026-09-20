from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import agents, auth, calibration, claims, debates
from app.config import settings
from app.database import engine
from app.models import Base


async def seed_system_agents():
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.agents import ARCHETYPE_MAP
    from app.agents.adlerian import AdlerianAgent
    from app.agents.analogist import AnalogistAgent
    from app.agents.bayesian import BayesianAgent
    from app.agents.contrarian import ContrarianAgent
    from app.agents.dialectician import DialecticianAgent
    from app.agents.falsificationist import FalsificationistAgent
    from app.agents.frequentist import FrequentistAgent
    from app.database import AsyncSessionLocal
    from app.models.agent import CognitiveAgent

    system_agents = [
        BayesianAgent(), FalsificationistAgent(), AnalogistAgent(),
        ContrarianAgent(), DialecticianAgent(), FrequentistAgent(),
        AdlerianAgent(),
    ]

    async with AsyncSessionLocal() as db:
        for agent_cls in system_agents:
            existing = await db.execute(
                select(CognitiveAgent).where(
                    CognitiveAgent.archetype == agent_cls.archetype,
                    CognitiveAgent.creator_id == None,
                )
            )
            if not existing.scalar_one_or_none():
                db.add(CognitiveAgent(
                    name=agent_cls.name,
                    archetype=agent_cls.archetype,
                    system_prompt=agent_cls.system_prompt,
                    description=agent_cls.description,
                    config={},
                    creator_id=None,
                    is_public=True,
                    reputation_score=1.0,
                ))
        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_system_agents()
    yield
    await engine.dispose()


app = FastAPI(title="Epistemic Marketplace", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(claims.router)
app.include_router(debates.router)
app.include_router(agents.router)
app.include_router(calibration.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
