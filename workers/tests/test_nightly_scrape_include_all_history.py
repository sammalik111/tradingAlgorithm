from dataclasses import replace
from datetime import UTC, date, datetime

import trading_workers.jobs.nightly_scrape as nightly_scrape
from trading_workers.models.enums import Chamber, SourceCode, TransactionType
from trading_workers.queue.messages import TradeIngestMessage
from trading_workers.scrapers.base import RawTradeRecord

RECENT_RECORD = RawTradeRecord(
    politician_full_name="Nancy Pelosi",
    chamber=Chamber.HOUSE,
    ticker="NVDA",
    asset_name="NVIDIA Corp",
    transaction_type=TransactionType.BUY,
    transaction_date=date(2026, 7, 1),
    disclosure_date=date(2026, 8, 1),
    amount_min=1000.0,
    amount_max=15000.0,
    source_code=SourceCode.HOUSE_STOCK_WATCHER,
    external_id=None,
    raw_payload={},
)
STALE_RECORD = replace(RECENT_RECORD, disclosure_date=date(2021, 1, 1))


class _FakeScraper:
    source_code = SourceCode.HOUSE_STOCK_WATCHER

    async def fetch(self) -> list[RawTradeRecord]:
        return [RECENT_RECORD, STALE_RECORD]


async def test_default_run_filters_out_stale_records(monkeypatch):
    enqueued: list[TradeIngestMessage] = []
    monkeypatch.setattr(nightly_scrape, "ALL_SCRAPERS", [_FakeScraper()])
    monkeypatch.setattr(nightly_scrape, "enqueue_trade", enqueued.append)

    results = await nightly_scrape.run_nightly_scrape(as_of=datetime(2026, 8, 15, tzinfo=UTC))

    assert len(enqueued) == 1
    assert results["house_stock_watcher"] == {"fetched": 2, "enqueued": 1}


async def test_include_all_history_bypasses_the_recency_filter(monkeypatch):
    enqueued: list[TradeIngestMessage] = []
    monkeypatch.setattr(nightly_scrape, "ALL_SCRAPERS", [_FakeScraper()])
    monkeypatch.setattr(nightly_scrape, "enqueue_trade", enqueued.append)

    results = await nightly_scrape.run_nightly_scrape(
        as_of=datetime(2026, 8, 15, tzinfo=UTC), include_all_history=True
    )

    assert len(enqueued) == 2
    assert results["house_stock_watcher"] == {"fetched": 2, "enqueued": 2}
