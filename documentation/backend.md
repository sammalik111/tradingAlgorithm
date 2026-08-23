# backend/

FastAPI application (`trading_backend`) providing the read API and the
nightly recommendation-scoring engine. Deployed as two separate Lambda
functions from the same container image, entered via different handlers
(see `documentation/infra.md`).

## Layout

```
backend/src/trading_backend/
  config.py                    Settings (pydantic-settings), env-driven
  main.py                      FastAPI app factory + API Gateway/Mangum handler
  db/
    base.py                    SQLAlchemy declarative base
    session.py                 Async engine/session factory
    secret_credentials.py      Resolves DATABASE_URL from Secrets Manager or env
  models/                      SQLAlchemy ORM models (see database-schema.md)
  schemas/                     Pydantic response models for the API
  api/
    router.py                  Aggregates all route modules
    deps.py                    FastAPI dependencies (DB session)
    routes/                    health, politicians, trades, recommendations
  algorithms/
    scoring.py                 Trade → per-ticker signal score
    clustering.py               Multi-politician consensus detection
  recommendation_engine/
    engine.py                   Orchestrates scoring + persistence + rationale
    lambda_handler.py           EventBridge entrypoint
  integrations/
    claude/
      client.py                 Anthropic client factory
      rationale.py               Builds the prompt, calls Claude, returns text
    robinhood/
      client.py                  Unimplemented stub (see below)
  cache/
    redis_client.py              JSON get/set helpers against ElastiCache
```

## Config (`config.py`)

`Settings` reads from environment variables (or a local `.env`). Notable
fields:

- `database_url` — set directly for local dev.
- `db_secret_arn` / `db_host` / `db_name` — set by Terraform in AWS; the
  password is fetched from the RDS-managed Secrets Manager secret via
  `db/secret_credentials.py` at first access and cached for the process
  lifetime.
- `anthropic_api_key` — required for `integrations/claude`; if unset,
  recommendation generation still runs but `rationale_text` is `null`.

## API (`api/`)

All routes are mounted under `/api/v1`.

| Route                              | Returns                                          |
| ----------------------------------- | ------------------------------------------------- |
| `GET /health`                       | `{"status": "ok"}`                                |
| `GET /politicians`                  | Tracked politicians (`?active_only=`)             |
| `GET /politicians/{id}`             | One politician                                    |
| `GET /trades`                       | Canonical (deduplicated) trades (`?ticker=`, `?politician_id=`, `?limit=`) |
| `GET /recommendations`              | Latest recommendations (`?ticker=`, `?limit=`)    |

`GET /recommendations` (no `ticker` filter) is cached in Redis under
`recommendations:latest` for `redis_cache_ttl_seconds` (default 300s),
since it's the frontend dashboard's main query and only changes once a
day.

## Scoring algorithm (`algorithms/scoring.py`)

Input: every `CanonicalTrade` for a ticker within a 90-day window
(`recommendation_engine/engine.py` loads this window).

For each trade:

```
recency_weight(t)  = 0.5 ** (days_ago / 21)          # halves every 21 days
size_weight(t)     = min(1, log10(amount_mid) / log10(5_000_000))
signal(t)          = sign(direction) * recency_weight(t) * size_weight(t)
```

Per-ticker aggregate:

```
raw_total     = sum(signal(t) for t in trades)
consensus     = count of distinct politicians agreeing on the majority direction
multiplier    = 1 + log1p(consensus - 1) * 0.35        # 1.0 if only one trader
boosted_total = raw_total * multiplier
signal_score  = tanh(boosted_total)                     # squashed to [-1, 1]
```

Bucketing (`algorithms/scoring.py`):

- `direction`: `BUY` if `signal_score >= 0.15`, `SELL` if `<= -0.15`, else `HOLD`.
- `conviction`: `HIGH` if `|signal_score| >= 0.6`, `MEDIUM` if `>= 0.3`, else `LOW`.

`algorithms/clustering.py` computes the consensus count: it groups the
distinct politician IDs trading a ticker by direction within the window
and returns the size of the largest group.

## Recommendation engine (`recommendation_engine/engine.py`)

`generate_recommendations(db, as_of)`:

1. Loads all `CanonicalTrade` rows with `transaction_date` in the last 90
   days, grouped by ticker.
2. Scores each group with `score_ticker`.
3. Calls `integrations/claude/rationale.generate_rationale` with the score
   and the supporting trades' politician names/dates/amount ranges.
4. Persists one `Recommendation` row per ticker plus a
   `RecommendationSupportingTrade` row per contributing `CanonicalTrade`,
   so every recommendation is traceable back to the trades that produced
   it.

`lambda_handler.py` wraps this in `asyncio.run` for the EventBridge
Scheduler entrypoint.

## Claude integration (`integrations/claude/`)

`client.py` builds an `AsyncAnthropic` client from `anthropic_api_key`;
raises `ClaudeNotConfiguredError` if unset (caught by the engine, not
propagated). `rationale.py` sends a fixed system prompt plus the ticker's
score and supporting trades, and returns the model's plain-text response
(model ID comes from `Settings.recommendation_model`, default
`claude-sonnet-5`).

## Robinhood integration (`integrations/robinhood/`)

Unimplemented on purpose. `RobinhoodClient` is a `Protocol` describing the
shape a future implementation must match (`get_positions()` today).
`UnconfiguredRobinhoodClient` (the only implementation) raises
`RobinhoodNotConfiguredError` on every call. No credential flow, no order
placement — this repo currently only produces read-only recommendations.

## Database migrations

`alembic/` manages the schema (single source of truth — `workers/`'s
mirrored models must be kept in sync manually, see
`documentation/database-schema.md`). `alembic/versions/0001_initial_schema.py`
creates every table. Run locally with:

```
cd backend
alembic upgrade head
```

In AWS, this runs as part of the weekly CodePipeline build
(`infra/codebuild/buildspec.yml`), not on every deploy of application code
alone.
