import uuid
from datetime import datetime

from pydantic import BaseModel


class DebateCreate(BaseModel):
    claim_id: uuid.UUID
    agent_archetypes: list[str] | None = None


class DebateResponse(BaseModel):
    id: uuid.UUID
    claim_id: uuid.UUID
    status: str
    agent_ids: list[uuid.UUID]
    final_belief_distribution: dict | None
    argument_graph: dict | None
    unknown_unknowns: list[str] | None
    created_at: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True
