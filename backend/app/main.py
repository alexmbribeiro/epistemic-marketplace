from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import agents, auth, calibration, claims, debates
from app.config import settings
from app.database import engine
from app.models import Base


async def seed_system_agents():
    from sqlalchemy import select

    from app.agents import ARCHETYPE_MAP, SEEDED_ARCHETYPES
    from app.database import AsyncSessionLocal
    from app.models.agent import CognitiveAgent

    async with AsyncSessionLocal() as db:
        for archetype in SEEDED_ARCHETYPES:
            agent = ARCHETYPE_MAP[archetype]()
            existing = await db.execute(
                select(CognitiveAgent).where(
                    CognitiveAgent.archetype == agent.archetype,
                    CognitiveAgent.creator_id == None,
                )
            )
            if not existing.scalar_one_or_none():
                db.add(CognitiveAgent(
                    name=agent.name,
                    archetype=agent.archetype,
                    system_prompt=agent.system_prompt,
                    description=agent.description,
                    config={},
                    creator_id=None,
                    is_public=True,
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
