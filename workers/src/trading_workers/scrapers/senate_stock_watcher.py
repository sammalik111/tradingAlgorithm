import re
from datetime import date, datetime

import httpx

from trading_workers.models.enums import Chamber, SourceCode
from trading_workers.scrapers.amount_ranges import parse_amount_range
from trading_workers.scrapers.base import RawTradeRecord
from trading_workers.scrapers.transaction_types import parse_transaction_type

# This mirror renders `ticker` and `asset_description` as HTML fragments for
# most rows (e.g. `<a href="...">PENN</a>`, or a bond's coupon/maturity as a
# nested <div>) rather than plain text -- confirmed against the live data:
# ~80% of tickers arrive wrapped like this, not an edge case.
_HTML_TAG = re.compile(r"<[^>]+>")


def _strip_html(raw: str) -> str:
    return _HTML_TAG.sub("", raw).strip()

# senatestockwatcher.com and its original S3-hosted dataset
# (senate-stock-watcher-data.s3-us-west-2.amazonaws.com) are both dead: the
# domain no longer resolves at all, and the bucket (while still resolving)
# now returns AccessDenied to anonymous requests. This points at a
# GitHub-hosted mirror of the same underlying dataset instead -- still free,
# no API key -- but as of this writing that mirror hasn't been updated
# since March 2021, so `fetch()` currently returns historical, not current,
# disclosures. `jobs/nightly_scrape.py`'s recency filter will (correctly)
# drop all of it on a normal run; pass `include_all_history=True` to that
# job to backfill it anyway. See documentation/workers.md.
DATA_URL = (
    "https://raw.githubusercontent.com/timothycarambat/senate-stock-watcher-data/"
    "master/aggregate/all_daily_summaries.json"
)


def _parse_date(raw: str) -> date:
    return datetime.strptime(raw, "%m/%d/%Y").date()


def _parse_transaction(
    transaction: dict,
    *,
    senator_full_name: str,
    disclosure_date: date,
    ptr_link: str | None,
) -> RawTradeRecord | None:
    ticker = _strip_html(transaction.get("ticker") or "").upper()
    if not ticker or ticker in ("--", "N/A"):
        return None

    asset_name = _strip_html(transaction.get("asset_description") or "") or ticker
    amount_min, amount_max = parse_amount_range(transaction.get("amount", ""))
    return RawTradeRecord(
        politician_full_name=senator_full_name,
        chamber=Chamber.SENATE,
        ticker=ticker,
        asset_name=asset_name,
        transaction_type=parse_transaction_type(transaction["type"]),
        transaction_date=_parse_date(transaction["transaction_date"]),
        disclosure_date=disclosure_date,
        amount_min=amount_min,
        amount_max=amount_max,
        source_code=SourceCode.SENATE_STOCK_WATCHER,
        external_id=ptr_link,
        raw_payload=transaction,
    )


class SenateStockWatcherScraper:
    """Pulls the Senate STOCK Act dataset from a GitHub-hosted mirror (see
    DATA_URL's comment for why this isn't the original senatestockwatcher.com
    site/S3 bucket). Free, no API key required.

    The response is one object per filing (a senator's PTR for one day),
    each carrying that filing's `date_recieved` (the disclosure date) and a
    nested list of individual transactions -- so every transaction in a
    filing shares one disclosure date.
    """

    source_code = SourceCode.SENATE_STOCK_WATCHER

    async def fetch(self) -> list[RawTradeRecord]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(DATA_URL)
            response.raise_for_status()
            filings = response.json()

        records: list[RawTradeRecord] = []
        for filing in filings:
            full_name = f"{filing.get('first_name', '')} {filing.get('last_name', '')}".strip()
            date_received = filing.get("date_recieved")
            if not full_name or not date_received:
                continue

            disclosure_date = _parse_date(date_received)
            ptr_link = filing.get("ptr_link")

            for transaction in filing.get("transactions", []):
                record = _parse_transaction(
                    transaction,
                    senator_full_name=full_name,
                    disclosure_date=disclosure_date,
                    ptr_link=ptr_link,
                )
                if record is not None:
                    records.append(record)

        return records
