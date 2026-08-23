from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from trading_workers.ingest.dedup import compute_dedup_key
from trading_workers.ingest.politician_resolver import resolve_politician
from trading_workers.models.canonical_trade import CanonicalTrade, CanonicalTradeSource
from trading_workers.models.raw_trade_event import RawTradeEvent
from trading_workers.models.source import Source
from trading_workers.scrapers.base import RawTradeRecord


async def ingest_record(
    db: AsyncSession, source: Source, record: RawTradeRecord
) -> CanonicalTrade | None:
    """Turn one scraped record into durable rows: always a `RawTradeEvent`
    for provenance, and an insert-or-merge into `CanonicalTrade` so the
    same disclosure reported by multiple sources is never double-counted.

    Returns `None` if this exact (source, disclosure) pair was already
    ingested on a previous run, so nightly re-scrapes of the full dataset
    stay idempotent.
    """
    politician = await resolve_politician(db, record)
    dedup_key = compute_dedup_key(
        politician.id,
        record.ticker,
        record.transaction_date,
        record.transaction_type,
        record.amount_min,
        record.amount_max,
    )

    already_ingested = await db.execute(
        select(RawTradeEvent.id).where(
            RawTradeEvent.source_id == source.id, RawTradeEvent.dedup_key == dedup_key
        )
    )
    if already_ingested.scalar_one_or_none() is not None:
        return None

    raw_event = RawTradeEvent(
        source_id=source.id,
        politician_id=politician.id,
        external_id=record.external_id,
        ticker_raw=record.ticker,
        asset_name_raw=record.asset_name,
        transaction_type_raw=record.transaction_type,
        transaction_date=record.transaction_date,
        disclosure_date=record.disclosure_date,
        amount_min=record.amount_min,
        amount_max=record.amount_max,
        raw_payload=record.raw_payload,
        dedup_key=dedup_key,
    )
    db.add(raw_event)
    await db.flush()

    now = datetime.now(UTC)
    canonical_result = await db.execute(
        select(CanonicalTrade).where(CanonicalTrade.dedup_key == dedup_key)
    )
    canonical = canonical_result.scalar_one_or_none()

    if canonical is None:
        amount_mid = (record.amount_min + record.amount_max) / 2
        canonical = CanonicalTrade(
            politician_id=politician.id,
            ticker=record.ticker,
            asset_name=record.asset_name,
            transaction_type=record.transaction_type,
            transaction_date=record.transaction_date,
            disclosure_date=record.disclosure_date,
            amount_min=record.amount_min,
            amount_max=record.amount_max,
            amount_mid=amount_mid,
            dedup_key=dedup_key,
            source_count=1,
            first_seen_at=now,
            last_seen_at=now,
        )
        db.add(canonical)
        await db.flush()
    else:
        canonical.source_count += 1
        canonical.last_seen_at = now

    db.add(
        CanonicalTradeSource(
            canonical_trade_id=canonical.id, raw_trade_event_id=raw_event.id, source_id=source.id
        )
    )
    return canonical
