from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from trading_workers.models.enums import SourceCode
from trading_workers.models.source import Source

_SOURCE_METADATA: dict[SourceCode, tuple[str, str]] = {
    SourceCode.SENATE_STOCK_WATCHER: ("Senate Stock Watcher", "https://senatestockwatcher.com"),
    SourceCode.HOUSE_STOCK_WATCHER: ("House Stock Watcher", "https://housestockwatcher.com"),
    SourceCode.QUIVER_QUANT: ("Quiver Quant", "https://www.quiverquant.com"),
    SourceCode.SEC_EDGAR: ("SEC EDGAR", "https://www.sec.gov/edgar"),
}


async def get_or_create_source(db: AsyncSession, source_code: SourceCode) -> Source:
    existing = await db.execute(select(Source).where(Source.code == source_code))
    source = existing.scalar_one_or_none()
    if source is not None:
        return source

    display_name, base_url = _SOURCE_METADATA[source_code]
    source = Source(code=source_code, display_name=display_name, base_url=base_url)
    db.add(source)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        existing = await db.execute(select(Source).where(Source.code == source_code))
        source = existing.scalar_one()

    return source
