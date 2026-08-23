import asyncio
import logging
from datetime import UTC, date, datetime, timedelta
from typing import Any

from trading_workers.queue.messages import TradeIngestMessage
from trading_workers.queue.sqs_client import enqueue_trade
from trading_workers.scrapers import ALL_SCRAPERS
from trading_workers.scrapers.base import RawTradeRecord

logger = logging.getLogger(__name__)

# senatestockwatcher.com / housestockwatcher.com republish the *entire*
# historical dataset every time, not just new disclosures. We only care
# about recently disclosed trades, and the STOCK Act gives filers up to 45
# days to disclose, so this window is wide enough to still catch a
# late-filed trade without re-enqueueing years of history every night.
DISCLOSURE_LOOKBACK_DAYS = 45


def _is_recent(record: RawTradeRecord, cutoff: date) -> bool:
    return record.disclosure_date >= cutoff


async def run_nightly_scrape(as_of: datetime | None = None) -> dict[str, Any]:
    """Fetch every configured source, filter to recently disclosed trades,
    and enqueue each onto the SQS ingest queue for `process_trade_message`
    to canonicalize.
    """
    cutoff = ((as_of or datetime.now(UTC)) - timedelta(days=DISCLOSURE_LOOKBACK_DAYS)).date()

    results: dict[str, Any] = {}
    for scraper in ALL_SCRAPERS:
        source_name = scraper.source_code.value
        try:
            records = await scraper.fetch()
        except Exception as exc:  # noqa: BLE001 - one source failing shouldn't sink the run
            logger.warning("scraper %s failed: %s", source_name, exc)
            results[source_name] = {"error": str(exc)}
            continue

        recent_records = [r for r in records if _is_recent(r, cutoff)]
        for record in recent_records:
            enqueue_trade(TradeIngestMessage.from_record(record))

        results[source_name] = {"fetched": len(records), "enqueued": len(recent_records)}

    return results


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """EventBridge Scheduler entrypoint, invoked nightly (see
    infra/modules/eventbridge).
    """
    return asyncio.run(run_nightly_scrape())
