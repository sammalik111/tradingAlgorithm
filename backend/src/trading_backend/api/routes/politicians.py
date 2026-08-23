import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from trading_backend.api.deps import DbSession
from trading_backend.models.politician import Politician
from trading_backend.schemas.politician import PoliticianOut

router = APIRouter(prefix="/politicians", tags=["politicians"])


@router.get("", response_model=list[PoliticianOut])
async def list_politicians(db: DbSession, active_only: bool = True) -> list[Politician]:
    stmt = select(Politician)
    if active_only:
        stmt = stmt.where(Politician.is_active.is_(True))
    result = await db.execute(stmt.order_by(Politician.full_name))
    return list(result.scalars().all())


@router.get("/{politician_id}", response_model=PoliticianOut)
async def get_politician(politician_id: uuid.UUID, db: DbSession) -> Politician:
    politician = await db.get(Politician, politician_id)
    if politician is None:
        raise HTTPException(status_code=404, detail="Politician not found")
    return politician
