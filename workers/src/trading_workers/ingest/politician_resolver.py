from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from trading_workers.ingest.name_normalization import normalize_politician_name
from trading_workers.models.politician import Politician
from trading_workers.scrapers.base import RawTradeRecord


async def resolve_politician(db: AsyncSession, record: RawTradeRecord) -> Politician:
    """Get-or-create the `Politician` row a scraped record belongs to,
    keyed on the source-agnostic normalized name so the same person
    scraped from multiple sources always resolves to one row.
    """
    normalized_name = normalize_politician_name(record.politician_full_name)

    existing = await db.execute(
        select(Politician).where(Politician.normalized_name == normalized_name)
    )
    politician = existing.scalar_one_or_none()
    if politician is not None:
        return politician

    politician = Politician(
        full_name=record.politician_full_name,
        normalized_name=normalized_name,
        chamber=record.chamber,
    )
    db.add(politician)
    try:
        await db.flush()
    except IntegrityError:
        # Lost a race with a concurrent worker inserting the same politician.
        await db.rollback()
        existing = await db.execute(
            select(Politician).where(Politician.normalized_name == normalized_name)
        )
        politician = existing.scalar_one()

    return politician
