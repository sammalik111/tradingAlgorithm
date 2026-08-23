# Overview

Monorepo (pnpm + turbo) with five top-level directories:

| Directory       | Language   | Purpose                                                            |
| --------------- | ---------- | ------------------------------------------------------------------- |
| `backend/`      | Python     | FastAPI read API + recommendation-scoring engine                    |
| `workers/`      | Python     | Nightly scrapers + SQS-driven ingest pipeline                       |
| `frontend/`     | TypeScript | React SPA that reads from the backend API                           |
| `infra/`        | Terraform  | Every AWS resource, organized as reusable modules                   |
| `documentation/`| Markdown   | This directory                                                      |

## Data flow

```
EventBridge (nightly, ~1am UTC)
        │
        ▼
 nightly-scrape Lambda (workers/jobs/nightly_scrape.py)
   - fetches Senate/House Stock Watcher + Quiver Quant
   - filters to disclosures from the last 45 days
   - publishes one SQS message per trade record
        │
        ▼
   SQS: trade-ingest queue
        │
        ▼
 process-trade-message Lambda (workers/jobs/process_trade_message.py)
   - resolves/creates the Politician row
   - writes a RawTradeEvent (always, per source)
   - upserts a CanonicalTrade keyed on a dedup hash
     (collapses the same disclosure reported by multiple sources)
        │
        ▼
      Aurora PostgreSQL (canonical_trades, raw_trade_events, ...)
        │
EventBridge (nightly, ~2 hours after the scrape)
        │
        ▼
 recommendation-engine Lambda (backend/recommendation_engine/engine.py)
   - reads canonical_trades from the last 90 days, grouped by ticker
   - scores each ticker (backend/algorithms/scoring.py)
   - asks Claude for a short rationale
   - writes a Recommendation row
        │
        ▼
 backend-api Lambda (FastAPI, behind API Gateway)
   - GET /api/v1/recommendations, /trades, /politicians
        │
        ▼
   frontend/ (static SPA on S3 + CloudFront)
```

## Deployment flow

Two independent triggers, both defined in `infra/`:

- **Nightly**: EventBridge Scheduler invokes `nightly-scrape` then
  `recommendation-engine` directly. This is data refresh, not a code
  deploy.
- **Weekly (or manual)**: EventBridge Scheduler starts the CodePipeline
  defined in `infra/modules/codepipeline`. It builds the backend and
  workers container images, runs Alembic migrations, builds and
  publishes the frontend, and updates all four Lambda functions. A
  normal `git push` does **not** trigger it (`DetectChanges = false` on
  the pipeline's source stage) — only the weekly schedule or a manual
  "Release change" in the CodePipeline console does.

See `documentation/backend.md`, `documentation/workers.md`,
`documentation/frontend.md`, `documentation/database-schema.md`, and
`documentation/infra.md` for each part in detail.
