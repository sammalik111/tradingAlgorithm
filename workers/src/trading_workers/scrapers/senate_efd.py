import asyncio
import re
from datetime import UTC, date, datetime, timedelta

import httpx
from bs4 import BeautifulSoup

from trading_workers.models.enums import Chamber, SourceCode
from trading_workers.scrapers.amount_ranges import parse_amount_range
from trading_workers.scrapers.base import RawTradeRecord
from trading_workers.scrapers.transaction_types import parse_transaction_type

ROOT = "https://efdsearch.senate.gov"
LANDING_PAGE_URL = f"{ROOT}/search/home/"
SEARCH_PAGE_URL = f"{ROOT}/search/"
REPORTS_DATA_URL = f"{ROOT}/search/report/data/"

# efdsearch.senate.gov's own internal numeric code for "Periodic
# Transaction Report" in its report_types filter. Undocumented by the site
# itself, but this exact value shows up consistently across independent
# open-source scrapers of this same endpoint (e.g.
# github.com/neelsomani/senator-filings, which this scraper's request/
# response handling is modeled on).
PERIODIC_TRANSACTION_REPORT_TYPE = 11

# Filings submitted on paper (a scanned image, not a machine-readable
# table) live under this URL prefix instead of a real HTML report --
# skipped, same as every other known scraper of this site.
PAPER_FILING_PREFIX = "/search/view/paper/"

BATCH_SIZE = 100
MAX_CONCURRENT_REPORT_FETCHES = 5

# Asked for directly in the search request itself, not just filtered
# client-side afterward -- keeps requests against a government server
# small and fast instead of pulling years of filing history every run.
# Matches jobs/nightly_scrape.py's own DISCLOSURE_LOOKBACK_DAYS.
LOOKBACK_DAYS = 45

_CSRF_TOKEN_RE = re.compile(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"')


def _extract_csrf_token(html: str) -> str:
    match = _CSRF_TOKEN_RE.search(html)
    if not match:
        raise RuntimeError(
            "Could not find csrfmiddlewaretoken on efdsearch.senate.gov's landing page "
            "-- the site's markup may have changed"
        )
    return match.group(1)


async def _accept_agreement_and_get_csrf(client: httpx.AsyncClient) -> str:
    """efdsearch.senate.gov requires accepting a terms-of-use agreement
    once per session before it serves search results -- this POST is what
    a browser sends when checking the "I agree" box. Returns the CSRF
    token, which the search endpoint also expects on every request.
    """
    landing = await client.get(LANDING_PAGE_URL)
    csrf_token = _extract_csrf_token(landing.text)

    await client.post(
        LANDING_PAGE_URL,
        data={"csrfmiddlewaretoken": csrf_token, "prohibition_agreement": "1"},
        headers={"Referer": LANDING_PAGE_URL},
    )
    return csrf_token


async def _fetch_report_rows(
    client: httpx.AsyncClient, csrf_token: str, submitted_start_date: str
) -> list[list]:
    rows: list[list] = []
    offset = 0
    while True:
        response = await client.post(
            REPORTS_DATA_URL,
            data={
                "start": str(offset),
                "length": str(BATCH_SIZE),
                "report_types": f"[{PERIODIC_TRANSACTION_REPORT_TYPE}]",
                "filer_types": "[]",
                "submitted_start_date": submitted_start_date,
                "submitted_end_date": "",
                "candidate_state": "",
                "senator_state": "",
                "office_id": "",
                "first_name": "",
                "last_name": "",
                "csrfmiddlewaretoken": csrf_token,
            },
            headers={"Referer": SEARCH_PAGE_URL},
        )
        response.raise_for_status()
        batch = response.json()["data"]
        if not batch:
            break
        rows.extend(batch)
        offset += BATCH_SIZE
    return rows


def _parse_row(row: list) -> tuple[str, str, date] | None:
    """One row = one filing. Returns (filer full name, report link,
    disclosure date), or None for a row this scraper doesn't handle (no
    usable link, or a paper/scanned filing with no machine-readable data).
    """
    first_name, last_name, _filer_type, link_html, date_received = row[:5]

    anchor = BeautifulSoup(link_html, "html.parser").find("a")
    href = anchor.get("href") if anchor else None
    if not isinstance(href, str) or not href or href.startswith(PAPER_FILING_PREFIX):
        return None

    full_name = f"{first_name} {last_name}".strip()
    disclosure_date = datetime.strptime(date_received, "%m/%d/%Y").date()
    return full_name, href, disclosure_date


async def _fetch_report_transactions(client: httpx.AsyncClient, href: str) -> list[dict]:
    response = await client.get(f"{ROOT}{href}")
    response.raise_for_status()
    if str(response.url).rstrip("/") == LANDING_PAGE_URL.rstrip("/"):
        # Redirected back to the agreement page: the session expired
        # mid-scrape. Rare enough (a single fetch() call runs in well
        # under the site's session lifetime) that this raises rather than
        # re-authenticating mid-flight -- jobs/nightly_scrape.py's
        # per-scraper error handling logs it and the next nightly run
        # gets a fresh session.
        raise RuntimeError("efdsearch.senate.gov session expired mid-scrape")

    tbody = BeautifulSoup(response.text, "html.parser").find("tbody")
    if tbody is None:
        return []

    transactions = []
    for row in tbody.find_all("tr"):
        cells = [cell.get_text(strip=True) for cell in row.find_all("td")]
        if len(cells) < 8:
            continue
        transactions.append(
            {
                "transaction_date": cells[1],
                "ticker": cells[3],
                "asset_name": cells[4],
                "transaction_type": cells[6],
                "amount": cells[7],
            }
        )
    return transactions


def _build_records(
    full_name: str, disclosure_date: date, href: str, transactions: list[dict]
) -> list[RawTradeRecord]:
    records = []
    for tx in transactions:
        ticker = (tx["ticker"] or "").strip().upper()
        if not ticker or ticker in ("--", "N/A"):
            continue
        try:
            transaction_date = datetime.strptime(tx["transaction_date"], "%m/%d/%Y").date()
        except ValueError:
            continue

        amount_min, amount_max = parse_amount_range(tx["amount"])
        records.append(
            RawTradeRecord(
                politician_full_name=full_name,
                chamber=Chamber.SENATE,
                ticker=ticker,
                asset_name=(tx["asset_name"] or ticker).strip(),
                transaction_type=parse_transaction_type(tx["transaction_type"]),
                transaction_date=transaction_date,
                disclosure_date=disclosure_date,
                amount_min=amount_min,
                amount_max=amount_max,
                source_code=SourceCode.SENATE_EFD,
                external_id=f"{ROOT}{href}",
                raw_payload=tx,
            )
        )
    return records


class SenateEfdScraper:
    """Pulls Senate STOCK Act Periodic Transaction Reports directly from
    the Senate's own official disclosure search (efdsearch.senate.gov) --
    the authoritative source senatestockwatcher.com itself used to scrape
    before that site went dark (see senate_stock_watcher.py's module
    docstring). Free, no API key, genuinely live -- unlike that GitHub
    mirror, which is real but frozen since March 2021.

    Flow: accept a one-time terms agreement to get a session cookie + CSRF
    token, query the site's DataTables search endpoint for recent
    Periodic Transaction Report filings, then fetch and parse each
    filing's own HTML page for its transaction line items. Paper-filed
    (scanned) reports have no machine-readable HTML and are skipped.
    """

    source_code = SourceCode.SENATE_EFD

    async def fetch(self) -> list[RawTradeRecord]:
        submitted_start_date = (
            (datetime.now(UTC) - timedelta(days=LOOKBACK_DAYS)).strftime("%m/%d/%Y") + " 00:00:00"
        )
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REPORT_FETCHES)

        async def process_row(client: httpx.AsyncClient, row: list) -> list[RawTradeRecord]:
            parsed = _parse_row(row)
            if parsed is None:
                return []
            full_name, href, disclosure_date = parsed

            async with semaphore:
                transactions = await _fetch_report_transactions(client, href)

            return _build_records(full_name, disclosure_date, href, transactions)

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            csrf_token = await _accept_agreement_and_get_csrf(client)
            rows = await _fetch_report_rows(client, csrf_token, submitted_start_date)
            results = await asyncio.gather(*(process_row(client, row) for row in rows))

        return [record for report_records in results for record in report_records]
