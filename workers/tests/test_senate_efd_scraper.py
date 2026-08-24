import respx
from httpx import Response

from trading_workers.models.enums import Chamber, SourceCode, TransactionType
from trading_workers.scrapers.senate_efd import (
    LANDING_PAGE_URL,
    REPORTS_DATA_URL,
    ROOT,
    SenateEfdScraper,
)

LANDING_PAGE_HTML = """
<html><body>
<form>
  <input type="hidden" name="csrfmiddlewaretoken" value="test-csrf-token">
</form>
</body></html>
"""

# One row per filing: [first_name, last_name, filer_type, link_html, date_received].
REPORT_ROWS_PAGE_1 = {
    "data": [
        [
            "Jane",
            "Doe",
            "Senator",
            '<a href="/search/view/ptr/11111111-1111-1111-1111-111111111111/">Report</a>',
            "08/10/2026",
        ],
        [
            "John",
            "Smith",
            "Senator",
            '<a href="/search/view/paper/22222222-2222-2222-2222-222222222222/">Report</a>',
            "08/09/2026",
        ],
    ]
}
REPORT_ROWS_PAGE_2 = {"data": []}

PTR_PAGE_HTML = """
<html><body>
<table>
<tbody>
<tr>
  <td>1</td>
  <td>07/26/2026</td>
  <td>Spouse</td>
  <td>NVDA</td>
  <td>NVIDIA Corp</td>
  <td>Stock</td>
  <td>Purchase</td>
  <td>$1,000,001 - $5,000,000</td>
</tr>
<tr>
  <td>2</td>
  <td>07/26/2026</td>
  <td>Self</td>
  <td>--</td>
  <td>Municipal Bond</td>
  <td>Bond</td>
  <td>Purchase</td>
  <td>$1,001 - $15,000</td>
</tr>
</tbody>
</table>
</body></html>
"""


@respx.mock
async def test_fetch_flow_end_to_end():
    respx.get(LANDING_PAGE_URL).mock(return_value=Response(200, text=LANDING_PAGE_HTML))
    respx.post(LANDING_PAGE_URL).mock(return_value=Response(200, text=""))
    respx.post(REPORTS_DATA_URL).mock(
        side_effect=[
            Response(200, json=REPORT_ROWS_PAGE_1),
            Response(200, json=REPORT_ROWS_PAGE_2),
        ]
    )
    respx.get(f"{ROOT}/search/view/ptr/11111111-1111-1111-1111-111111111111/").mock(
        return_value=Response(200, text=PTR_PAGE_HTML)
    )

    # The paper-filed row (John Smith) is never mocked, so respx would
    # raise if the scraper tried to request it -- this implicitly proves
    # paper filings are skipped, not fetched.
    records = await SenateEfdScraper().fetch()

    assert len(records) == 1
    record = records[0]
    assert record.politician_full_name == "Jane Doe"
    assert record.chamber == Chamber.SENATE
    assert record.ticker == "NVDA"
    assert record.asset_name == "NVIDIA Corp"
    assert record.transaction_type == TransactionType.BUY
    assert record.transaction_date.isoformat() == "2026-07-26"
    assert record.disclosure_date.isoformat() == "2026-08-10"
    assert record.amount_min == 1_000_001.0
    assert record.amount_max == 5_000_000.0
    assert record.source_code == SourceCode.SENATE_EFD
    assert record.external_id == f"{ROOT}/search/view/ptr/11111111-1111-1111-1111-111111111111/"


@respx.mock
async def test_fetch_paginates_until_an_empty_page():
    respx.get(LANDING_PAGE_URL).mock(return_value=Response(200, text=LANDING_PAGE_HTML))
    respx.post(LANDING_PAGE_URL).mock(return_value=Response(200, text=""))
    page_route = respx.post(REPORTS_DATA_URL)
    page_route.side_effect = [
        Response(200, json=REPORT_ROWS_PAGE_1),
        Response(200, json=REPORT_ROWS_PAGE_2),
    ]
    respx.get(f"{ROOT}/search/view/ptr/11111111-1111-1111-1111-111111111111/").mock(
        return_value=Response(200, text=PTR_PAGE_HTML)
    )

    await SenateEfdScraper().fetch()

    assert page_route.call_count == 2
