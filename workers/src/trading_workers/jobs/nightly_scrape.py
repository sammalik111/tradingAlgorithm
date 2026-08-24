import asyncio
import logging
from datetime import UTC, date, datetime, timedelta
from typing import Any

from trading_workers.queue.messages import TradeIngestMessage
from trading_workers.queue.sqs_client import enqueue_trade
from trading_workers.scrapers import ALL_SCRAPERS
from trading_workers.scrapers.base import RawTradeRecord
from trading_workers.scrapers.quiver_quant import QuiverQuantNotConfiguredError

logger = logging.getLogger(__name__)

# housestockwatcher.com (when it's reachable at all -- see
# HouseStockWatcherScraper) republishes its *entire* historical dataset
# every time, not just new disclosures; SenateEfdScraper asks the source
# for only-recent filings directly instead (see its own LOOKBACK_DAYS),
# so this filter is mostly a backstop for it. We only care about recently
# disclosed trades either way, and the STOCK Act gives filers up to 45
# days to disclose, so this window is wide enough to still catch a
# late-filed trade without re-enqueueing years of history every night.
DISCLOSURE_LOOKBACK_DAYS = 45


def _is_recent(record: RawTradeRecord, cutoff: date) -> bool:
    return record.disclosure_date >= cutoff


async def run_nightly_scrape(
    as_of: datetime | None = None, include_all_history: bool = False
) -> dict[str, Any]:
    """Fetch every configured source, filter to recently disclosed trades,
    and enqueue each onto the SQS ingest queue for `process_trade_message`
    to canonicalize.

    `include_all_history=True` skips the recency filter entirely and
    enqueues everything a scraper returns, regardless of disclosure date.
    Meant for a one-off manual backfill of a scraper that returns full
    history rather than just-recent filings (e.g.
    `HouseStockWatcherScraper`, when its source is reachable at all -- see
    its module docstring), not for the real nightly schedule.
    """
    cutoff = ((as_of or datetime.now(UTC)) - timedelta(days=DISCLOSURE_LOOKBACK_DAYS)).date()

    results: dict[str, Any] = {}
    for scraper in ALL_SCRAPERS:
        source_name = scraper.source_code.value
        try:
            records = await scraper.fetch()
        except QuiverQuantNotConfiguredError:
            # Optional paid source with no key set -- expected, not a
            # failure. Logged quietly so it doesn't read as a broken
            # scraper; starts fetching automatically the moment
            # QUIVER_QUANT_API_KEY is populated, no code change needed.
            logger.info("scraper %s skipped: not configured", source_name)
            results[source_name] = {"skipped": "not configured"}
            continue
        except Exception as exc:  # noqa: BLE001 - one source failing shouldn't sink the run
            logger.warning("scraper %s failed: %s", source_name, exc)
            results[source_name] = {"error": str(exc)}
            continue

        surviving_records = (
            records if include_all_history else [r for r in records if _is_recent(r, cutoff)]
        )
        for record in surviving_records:
            enqueue_trade(TradeIngestMessage.from_record(record))

        results[source_name] = {"fetched": len(records), "enqueued": len(surviving_records)}

    return results


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """EventBridge Scheduler entrypoint, invoked nightly (see
    infra/modules/eventbridge). `event["include_all_history"]` is only
    meaningful on a manual `aws lambda invoke` for a one-off backfill --
    the EventBridge schedule always invokes with an empty payload.
    """
    include_all_history = bool(event.get("include_all_history", False))
    return asyncio.run(run_nightly_scrape(include_all_history=include_all_history))
