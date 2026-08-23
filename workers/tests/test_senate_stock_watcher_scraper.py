import respx
from httpx import Response

from trading_workers.models.enums import Chamber, SourceCode, TransactionType
from trading_workers.scrapers.senate_stock_watcher import DATA_URL, SenateStockWatcherScraper

FIXTURE_PAYLOAD = [
    {
        "senator": "Nancy Pelosi",
        "ticker": "NVDA",
        "asset_description": "NVIDIA Corp",
        "type": "Purchase",
        "amount": "$1,000,001 - $5,000,000",
        "transaction_date": "07/26/2026",
        "disclosure_date": "08/10/2026",
        "ptr_link": "https://example.com/ptr/1",
    },
    {
        "senator": "Some Senator",
        "ticker": "--",
        "asset_description": "Municipal Bond",
        "type": "Purchase",
        "amount": "$1,001 - $15,000",
        "transaction_date": "07/26/2026",
        "disclosure_date": "08/10/2026",
        "ptr_link": "https://example.com/ptr/2",
    },
]


@respx.mock
async def test_fetch_parses_records_and_skips_non_ticker_rows():
    respx.get(DATA_URL).mock(return_value=Response(200, json=FIXTURE_PAYLOAD))

    records = await SenateStockWatcherScraper().fetch()

    assert len(records) == 1
    record = records[0]
    assert record.politician_full_name == "Nancy Pelosi"
    assert record.chamber == Chamber.SENATE
    assert record.ticker == "NVDA"
    assert record.transaction_type == TransactionType.BUY
    assert record.amount_min == 1_000_001.0
    assert record.amount_max == 5_000_000.0
    assert record.source_code == SourceCode.SENATE_STOCK_WATCHER
