# workers/

Independent Python app (`trading_workers`) that owns all data-pull logic:
scraping public trade disclosures and turning them into rows in Aurora.
Deployed as two Lambda functions from one container image (nightly-scrape,
process-trade-message).

## Layout

```
workers/src/trading_workers/
  config.py                     Settings, same pattern as backend/
  models/                       Mirrors backend/'s schema for the tables
                                 workers writes to (sources, politicians,
                                 raw_trade_events, canonical_trades)
  db/
    session.py, secret_credentials.py   Same as backend/
  scrapers/
    base.py                     RawTradeRecord dataclass + Scraper protocol
    amount_ranges.py             Parses "$1,001 - $15,000" style strings
    transaction_types.py         Maps free-text type → TransactionType enum
    senate_stock_watcher.py       Free source, no API key
    house_stock_watcher.py        Free source, no API key
    quiver_quant.py                Paid source, gated on QUIVER_QUANT_API_KEY
  ingest/
    name_normalization.py         Collapses name variants to one lookup key
    politician_resolver.py         Get-or-create Politician by normalized name
    source_resolver.py             Get-or-create Source row per SourceCode
    dedup.py                       Computes the cross-source dedup key
    canonicalizer.py                Raw record → RawTradeEvent + CanonicalTrade
  queue/
    messages.py                    TradeIngestMessage (SQS wire format)
    sqs_client.py                   enqueue_trade()
  jobs/
    nightly_scrape.py               EventBridge entrypoint (producer)
    process_trade_message.py         SQS entrypoint (consumer)
```

## Scrapers (`scrapers/`)

Each scraper implements `async fetch() -> list[RawTradeRecord]` and
declares a `source_code`. `scrapers/__init__.py:ALL_SCRAPERS` lists every
scraper the nightly job runs.

| Scraper                    | Source                                                        | Auth |
| --------------------------- | --------------------------------------------------------------- | ---- |
| `SenateStockWatcherScraper` | `raw.githubusercontent.com/timothycarambat/senate-stock-watcher-data` (see caveat below) | none |
| `HouseStockWatcherScraper`  | `house-stock-watcher-data.s3-us-west-2.amazonaws.com` (**dead** — see caveat below) | none |
| `QuiverQuantScraper`        | `api.quiverquant.com/beta/live/congresstrading`                  | `QUIVER_QUANT_API_KEY` |

Both watcher datasets are (or were) the **entire historical dataset**, not
a daily delta — `jobs/nightly_scrape.py` filters to `disclosure_date`
within the last 45 days (`DISCLOSURE_LOOKBACK_DAYS`) before enqueueing, so
nightly volume stays bounded to genuinely recent activity while still
catching a late-filed disclosure (STOCK Act allows up to 45 days to file).

If `QuiverQuantScraper` raises `QuiverQuantNotConfiguredError` (no API
key set), `nightly_scrape.py` reports it as `{"skipped": "not configured"}`
— an expected, quiet no-op, not an error — and continues with the other
sources. It starts fetching automatically the moment `QUIVER_QUANT_API_KEY`
is populated; no code change needed either way. Any other scraper
exception is a genuine failure: logged as a warning and reported as
`{"error": ...}`, without blocking the rest of the run.

**Free-source caveat (as of this writing):** both `senatestockwatcher.com`
and `housestockwatcher.com` — and their original S3-hosted datasets — are
dead (the domains no longer resolve; the S3 buckets return `AccessDenied`
to anonymous requests even when reachable directly). `SenateStockWatcherScraper`
now pulls from a GitHub-hosted mirror of the same underlying data instead,
but that mirror itself hasn't been updated since **March 2021** — it's
alive and returns valid JSON, but every disclosure in it is 5+ years
stale, so the normal 45-day recency filter drops all of it on a real
nightly run. No free replacement was found for House data at all. To
seed the pipeline with this historical Senate data anyway (for testing
the recommendation engine / frontend end-to-end, not for real trading
signal), invoke `nightly-scrape` with `{"include_all_history": true}` —
see `jobs/nightly_scrape.py`'s `run_nightly_scrape`. A genuinely live free
replacement would mean scraping the actual government sources directly
(`efdsearch.senate.gov`, `disclosures-clerk.house.gov`) — real engineering,
not implemented here.

One more quirk of the GitHub mirror: roughly 80% of its `ticker` fields
arrive as an HTML anchor tag (e.g. `<a href="...">PENN</a>`) rather than
plain text — `senate_stock_watcher.py`'s `_strip_html` strips markup from
both `ticker` and `asset_description` before use. Confirmed against the
live data, not a hypothetical edge case.

## Ingest pipeline (`ingest/`)

This is where "segregate by source, collapse duplicates" is implemented.

1. **`name_normalization.normalize_politician_name`** — lowercases,
   flips `"Last, First"` to `"first last"`, strips titles
   (`Hon.`, `Sen.`, ...) and suffixes (`Jr.`, `III`, ...), so the same
   person scraped from different sources resolves to one row.
2. **`politician_resolver.resolve_politician`** — get-or-create on
   `Politician.normalized_name`.
3. **`dedup.compute_dedup_key`** — SHA-256 of
   `politician_id | ticker | transaction_date | transaction_type | amount_min | amount_max`.
   This key is **source-agnostic**: two sources reporting the same
   disclosure produce the same key.
4. **`canonicalizer.ingest_record`**:
   - Looks up `RawTradeEvent` by `(source_id, dedup_key)`. If found,
     this exact (source, disclosure) pair was already ingested on a
     previous run — returns `None` (idempotent re-scrapes).
   - Otherwise inserts a new `RawTradeEvent` (always, one per source —
     this is the "segregated by source" record, kept forever for
     provenance).
   - Looks up `CanonicalTrade` by `dedup_key` (source-agnostic). If
     found, increments `source_count` and updates `last_seen_at` instead
     of inserting a duplicate. If not found, inserts a new
     `CanonicalTrade` with `source_count = 1`.
   - Inserts a `CanonicalTradeSource` row linking the two, so every
     canonical trade can still be traced back to every raw event/source
     that contributed to it.

The backend's recommendation engine only ever reads `canonical_trades`,
so a trade reported by three sources contributes to the score once, not
three times.

## Queue (`queue/`)

`TradeIngestMessage` is a 1:1 pydantic mirror of `RawTradeRecord`
(`from_record`/`to_record` convert between them). `sqs_client.enqueue_trade`
publishes it as JSON to `TRADE_INGEST_QUEUE_URL`.

## Jobs (`jobs/`)

- **`nightly_scrape.handler`** (EventBridge trigger): runs every scraper,
  filters by disclosure date, enqueues each surviving record.
- **`process_trade_message.handler`** (SQS trigger): for each message in
  the batch, resolves the `Source` row, calls `ingest_record`, and
  commits. Returns SQS's `batchItemFailures` format so only messages that
  actually failed are redelivered, not the whole batch.
