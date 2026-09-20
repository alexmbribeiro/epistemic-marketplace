import uuid
from datetime import datetime

from pydantic import BaseModel


class DebateCreate(BaseModel):
    claim_id: uuid.UUID
    # Preferred: pick exact agents, which is the only way a user-authored one
    # can take part. agent_archetypes stays for the seeded six.
    agent_ids: list[uuid.UUID] | None = None
    agent_archetypes: list[str] | None = None


class DebateResponse(BaseModel):
    id: uuid.UUID
    claim_id: uuid.UUID
    claim_content: str | None = None
    claim_category: str | None = None
    status: str
    agent_ids: list[uuid.UUID]
    final_belief_distribution: dict | None
    argument_graph: dict | None
    unknown_unknowns: list[str] | None
    synthesis: dict | None
    created_at: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True
