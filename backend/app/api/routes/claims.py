import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.claim import Claim
from app.models.user import User
from app.schemas.claim import ClaimCreate, ClaimResponse

router = APIRouter(prefix="/claims", tags=["claims"])


@router.post("/", response_model=ClaimResponse, status_code=201)
async def create_claim(
    body: ClaimCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    claim = Claim(
        content=body.content,
        category=body.category,
        is_verifiable=body.is_verifiable,
        creator_id=current_user.id if current_user else None,
    )
    db.add(claim)
    await db.commit()
    await db.refresh(claim)
    return claim


@router.get("/", response_model=list[ClaimResponse])
async def list_claims(db: AsyncSession = Depends(get_db), limit: int = 20, offset: int = 0):
    result = await db.execute(select(Claim).order_by(Claim.created_at.desc()).limit(limit).offset(offset))
    return result.scalars().all()


@router.get("/{claim_id}", response_model=ClaimResponse)
async def get_claim(claim_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Claim).where(Claim.id == claim_id))
    claim = result.scalar_one_or_none()
    if not claim:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim
