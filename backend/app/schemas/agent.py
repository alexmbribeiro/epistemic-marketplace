import uuid
from datetime import datetime

from pydantic import BaseModel


class AgentCreate(BaseModel):
    name: str
    archetype: str = "custom"
    system_prompt: str
    description: str
    config: dict = {}
    is_public: bool = True


class AgentResponse(BaseModel):
    id: uuid.UUID
    name: str
    archetype: str
    description: str
    config: dict
    is_public: bool
    reputation_score: float
    creator_id: uuid.UUID | None
    created_at: datetime

    class Config:
        from_attributes = True
