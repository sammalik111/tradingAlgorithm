from datetime import datetime

import httpx

from trading_workers.models.enums import Chamber, SourceCode
from trading_workers.scrapers.amount_ranges import parse_amount_range
from trading_workers.scrapers.base import RawTradeRecord
from trading_workers.scrapers.transaction_types import parse_transaction_type

DATA_URL = "https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/all_transactions.json"


def _parse_date(raw: str) -> datetime:
    return datetime.strptime(raw, "%Y-%m-%d")


def _parse_record(item: dict) -> RawTradeRecord | None:
    ticker = (item.get("ticker") or "").strip().upper()
    if not ticker or ticker in ("--", "N/A"):
        return None

    amount_min, amount_max = parse_amount_range(item.get("amount", ""))
    return RawTradeRecord(
        politician_full_name=item["representative"].strip(),
        chamber=Chamber.HOUSE,
        ticker=ticker,
        asset_name=(item.get("asset_description") or ticker).strip(),
        transaction_type=parse_transaction_type(item["type"]),
        transaction_date=_parse_date(item["transaction_date"]).date(),
        disclosure_date=_parse_date(item["disclosure_date"]).date(),
        amount_min=amount_min,
        amount_max=amount_max,
        source_code=SourceCode.HOUSE_STOCK_WATCHER,
        external_id=item.get("ptr_link"),
        raw_payload=item,
    )


class HouseStockWatcherScraper:
    """Pulls the full congressional trading dataset published by
    housestockwatcher.com, which aggregates House STOCK Act disclosures
    (disclosures-clerk.house.gov). Free, no API key required.
    """

    source_code = SourceCode.HOUSE_STOCK_WATCHER

    async def fetch(self) -> list[RawTradeRecord]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(DATA_URL)
            response.raise_for_status()
            items = response.json()

        records = (_parse_record(item) for item in items)
        return [record for record in records if record is not None]
