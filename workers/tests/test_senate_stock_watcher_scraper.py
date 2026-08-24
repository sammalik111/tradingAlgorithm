import respx
from httpx import Response

from trading_workers.models.enums import Chamber, SourceCode, TransactionType
from trading_workers.scrapers.senate_stock_watcher import DATA_URL, SenateStockWatcherScraper

FIXTURE_PAYLOAD = [
    {
        "first_name": "Nancy",
        "last_name": "Pelosi",
        "office": "Pelosi, Nancy (Senator)",
        "ptr_link": "https://example.com/ptr/1",
        "date_recieved": "08/10/2026",
        "transactions": [
            {
                "transaction_date": "07/26/2026",
                "owner": "Spouse",
                # The mirror wraps most tickers in an anchor tag like this.
                "ticker": '<a href="https://finance.yahoo.com/q?s=NVDA" target="_blank">NVDA</a>',
                "asset_description": "NVIDIA Corp",
                "asset_type": "Stock",
                "type": "Purchase",
                "amount": "$1,000,001 - $5,000,000",
                "comment": "--",
            },
            {
                "transaction_date": "07/26/2026",
                "owner": "Spouse",
                "ticker": "--",
                "asset_description": "Municipal Bond",
                "asset_type": "Bond",
                "type": "Purchase",
                "amount": "$1,001 - $15,000",
                "comment": "--",
            },
        ],
        "bioguide": "P000197",
    },
    {
        "first_name": "Someone",
        "last_name": "Who Filed Late",
        "office": "Who Filed Late, Someone (Senator)",
        "ptr_link": "https://example.com/ptr/2",
        "date_recieved": "08/10/2026",
        "transactions": [],
        "bioguide": "W000000",
    },
]


@respx.mock
async def test_fetch_flattens_filings_and_skips_non_ticker_rows():
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
    assert record.external_id == "https://example.com/ptr/1"
    # disclosure_date comes from the filing, not the transaction.
    assert record.disclosure_date.isoformat() == "2026-08-10"


@respx.mock
async def test_fetch_strips_html_wrapping_from_ticker():
    respx.get(DATA_URL).mock(return_value=Response(200, json=FIXTURE_PAYLOAD))

    records = await SenateStockWatcherScraper().fetch()

    assert records[0].ticker == "NVDA"
    assert "<" not in records[0].ticker


@respx.mock
async def test_fetch_skips_filings_with_no_transactions():
    respx.get(DATA_URL).mock(return_value=Response(200, json=FIXTURE_PAYLOAD))

    records = await SenateStockWatcherScraper().fetch()

    assert all(r.politician_full_name != "Someone Who Filed Late" for r in records)
