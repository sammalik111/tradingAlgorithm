from dataclasses import replace
from datetime import date

from trading_workers.jobs.nightly_scrape import _is_recent
from trading_workers.models.enums import Chamber, SourceCode, TransactionType
from trading_workers.scrapers.base import RawTradeRecord

BASE_RECORD = RawTradeRecord(
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


def test_recent_disclosure_passes():
    assert _is_recent(BASE_RECORD, cutoff=date(2026, 7, 15))


def test_old_disclosure_is_filtered_out():
    stale = replace(BASE_RECORD, disclosure_date=date(2026, 1, 1))
    assert not _is_recent(stale, cutoff=date(2026, 7, 15))
