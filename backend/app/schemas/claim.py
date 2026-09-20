import uuid
from datetime import datetime

from pydantic import BaseModel


class ClaimCreate(BaseModel):
    content: str
    category: str = "other"
    is_verifiable: bool = False


class ClaimResponse(BaseModel):
    id: uuid.UUID
    content: str
    category: str
    status: str
    is_verifiable: bool
    created_at: datetime

    class Config:
        from_attributes = True
