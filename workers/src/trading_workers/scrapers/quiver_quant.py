from datetime import datetime

import httpx

from trading_workers.config import get_settings
from trading_workers.models.enums import Chamber, SourceCode
from trading_workers.scrapers.amount_ranges import parse_amount_range
from trading_workers.scrapers.base import RawTradeRecord
from trading_workers.scrapers.transaction_types import parse_transaction_type

DATA_URL = "https://api.quiverquant.com/beta/live/congresstrading"

_CHAMBER_BY_HOUSE_FIELD = {"House": Chamber.HOUSE, "Senate": Chamber.SENATE}


class QuiverQuantNotConfiguredError(RuntimeError):
    """Raised when QUIVER_QUANT_API_KEY is unset. Quiver is a paid
    third-party aggregator layered on top of the same public disclosures
    the free watcher scrapers already cover, so it's optional: leave it
    unconfigured and the nightly job simply skips it.
    """


def _parse_record(item: dict) -> RawTradeRecord | None:
    ticker = (item.get("Ticker") or "").strip().upper()
    if not ticker:
        return None

    amount_min, amount_max = parse_amount_range(item.get("Range", ""))
    return RawTradeRecord(
        politician_full_name=item["Representative"].strip(),
        chamber=_CHAMBER_BY_HOUSE_FIELD.get(item.get("House", ""), Chamber.HOUSE),
        ticker=ticker,
        asset_name=ticker,
        transaction_type=parse_transaction_type(item["Transaction"]),
        transaction_date=datetime.strptime(item["TransactionDate"], "%Y-%m-%d").date(),
        disclosure_date=datetime.strptime(item["ReportDate"], "%Y-%m-%d").date(),
        amount_min=amount_min,
        amount_max=amount_max,
        source_code=SourceCode.QUIVER_QUANT,
        external_id=item.get("ID"),
        raw_payload=item,
    )


class QuiverQuantScraper:
    """Optional paid data source (api.quiverquant.com) covering the same
    congressional disclosures as the free watcher scrapers, plus faster
    turnaround on some filings. Requires `QUIVER_QUANT_API_KEY`.
    """

    source_code = SourceCode.QUIVER_QUANT

    async def fetch(self) -> list[RawTradeRecord]:
        settings = get_settings()
        if not settings.quiver_quant_api_key:
            raise QuiverQuantNotConfiguredError("QUIVER_QUANT_API_KEY is not set")

        headers = {"Authorization": f"Bearer {settings.quiver_quant_api_key}"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(DATA_URL, headers=headers)
            response.raise_for_status()
            items = response.json()

        records = (_parse_record(item) for item in items)
        return [record for record in records if record is not None]
