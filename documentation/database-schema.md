# Database schema

Aurora PostgreSQL. Schema owned by `backend/alembic` (migrations are only
ever generated/run from `backend/`); `workers/`'s ORM models
(`workers/src/trading_workers/models/`) map to the same tables and must be
kept in sync by hand when the schema changes.

## Tables

### `sources`

One row per data provider. Referenced by `raw_trade_events` and
`canonical_trade_sources` so every raw record and every contribution to a
canonical trade is attributable to where it came from.

| Column         | Type                                                                                                                       |
| -------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `id`           | uuid, PK                                                                                                                   |
| `code`         | enum: `senate_stock_watcher`, `house_stock_watcher`, `quiver_quant`, `sec_edgar`, `senate_efd` (added in migration `0003`) |
| `display_name` | text                                                                                                                       |
| `base_url`     | text                                                                                                                       |

### `politicians`

One row per tracked person, deduplicated across sources by
`normalized_name` (see `workers/ingest/name_normalization.py`).

| Column            | Type                                 |
| ----------------- | ------------------------------------ |
| `id`              | uuid, PK                             |
| `full_name`       | text — as first seen                 |
| `normalized_name` | text, unique — lookup key            |
| `chamber`         | enum: `house`, `senate`, `executive` |
| `party`           | text, nullable                       |
| `state`           | text(2), nullable                    |
| `bioguide_id`     | text, nullable, unique               |
| `is_active`       | boolean                              |

### `raw_trade_events`

One row per (source, disclosure) — **never deduplicated across sources**.
This is the "segregated by source" record: every scrape that reports a
trade gets its own row here, forever, for provenance.

| Column                     | Type                                                                                                     |
| -------------------------- | -------------------------------------------------------------------------------------------------------- |
| `id`                       | uuid, PK                                                                                                 |
| `source_id`                | uuid, FK → `sources.id`                                                                                  |
| `politician_id`            | uuid, FK → `politicians.id`                                                                              |
| `external_id`              | text, nullable — source's own record id/link if it has one                                               |
| `ticker_raw`               | text                                                                                                     |
| `asset_name_raw`           | text                                                                                                     |
| `transaction_type_raw`     | enum: `buy`, `sell`, `exchange`                                                                          |
| `transaction_date`         | date                                                                                                     |
| `disclosure_date`          | date                                                                                                     |
| `amount_min`, `amount_max` | numeric(16,2) — the STOCK Act disclosure bracket                                                         |
| `raw_payload`              | jsonb — the untouched scraped record                                                                     |
| `dedup_key`                | text, indexed — same formula as `canonical_trades.dedup_key`, scoped per source for idempotent re-ingest |

Unique in practice (not DB-enforced) per `(source_id, dedup_key)` —
`workers/ingest/canonicalizer.py` checks this pair before inserting, so
re-scraping the same disclosure from the same source is a no-op.

### `canonical_trades`

One row per disclosed trade, **collapsed across every source that
reported it**. The recommendation engine reads only this table.

| Column                                   | Type                                                                                                                     |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `id`                                     | uuid, PK                                                                                                                 |
| `politician_id`                          | uuid, FK → `politicians.id`                                                                                              |
| `ticker`                                 | text                                                                                                                     |
| `asset_name`                             | text                                                                                                                     |
| `transaction_type`                       | enum: `buy`, `sell`, `exchange`                                                                                          |
| `transaction_date`                       | date                                                                                                                     |
| `disclosure_date`                        | date                                                                                                                     |
| `amount_min`, `amount_max`, `amount_mid` | numeric(16,2)                                                                                                            |
| `dedup_key`                              | text, **unique** — `sha256(politician_id \| ticker \| transaction_date \| transaction_type \| amount_min \| amount_max)` |
| `source_count`                           | integer — how many distinct sources reported this trade                                                                  |
| `first_seen_at`, `last_seen_at`          | timestamptz                                                                                                              |

### `canonical_trade_sources`

Join table: which raw events (and therefore which sources) contributed to
a given canonical trade. Lets you answer "was this trade reported by
multiple sources?" without losing the collapsing behavior above.

| Column               | Type                             |
| -------------------- | -------------------------------- |
| `id`                 | uuid, PK                         |
| `canonical_trade_id` | uuid, FK → `canonical_trades.id` |
| `raw_trade_event_id` | uuid, FK → `raw_trade_events.id` |
| `source_id`          | uuid, FK → `sources.id`          |

Unique on `(canonical_trade_id, raw_trade_event_id)`.

### `recommendations`

One row per ticker per recommendation-engine run.

| Column           | Type                                                            |
| ---------------- | --------------------------------------------------------------- |
| `id`             | uuid, PK                                                        |
| `ticker`         | text                                                            |
| `generated_at`   | timestamptz                                                     |
| `signal_score`   | numeric(6,4) — see `documentation/backend.md`                   |
| `conviction`     | enum: `low`, `medium`, `high`                                   |
| `direction`      | enum: `buy`, `sell`, `hold`                                     |
| `rationale_text` | text, nullable — Claude output, null if Claude isn't configured |
| `model_version`  | text — the Claude model used                                    |

### `recommendation_supporting_trades`

Join table: which `canonical_trades` fed a given recommendation's score.

| Column               | Type                             |
| -------------------- | -------------------------------- |
| `id`                 | uuid, PK                         |
| `recommendation_id`  | uuid, FK → `recommendations.id`  |
| `canonical_trade_id` | uuid, FK → `canonical_trades.id` |

### `simulated_orders`

Paper-trade log entries against a recommendation. No real brokerage is
ever called (see `documentation/backend.md`'s "Simulated trade logging"
section) — `price` is whatever the caller previewed/confirmed at, not a
fetched market quote, since this repo has no market-data integration.

| Column              | Type                                                     |
| ------------------- | -------------------------------------------------------- |
| `id`                | uuid, PK                                                 |
| `recommendation_id` | uuid, FK → `recommendations.id`                          |
| `ticker`            | text                                                     |
| `side`              | enum: `buy`, `sell`                                      |
| `quantity`          | numeric(16,4)                                            |
| `price`             | numeric(16,2) — caller-supplied, not a real market quote |
| `notional_value`    | numeric(16,2) — `quantity * price`                       |

## Entity relationships

```
sources ──< raw_trade_events >── politicians
                  │
                  │ (via canonical_trade_sources)
                  ▼
           canonical_trades >── politicians
                  │
                  │ (via recommendation_supporting_trades)
                  ▼
             recommendations ──< simulated_orders
```
