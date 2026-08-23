# Trading Recommendation Platform

Tracks publicly disclosed trades from tracked politicians (Senate/House
STOCK Act filings, plus an optional paid aggregator) and turns them into
scored buy/sell/hold recommendations with a Claude-generated rationale.

See `documentation/overview.md` for the full architecture and data flow.

## Repo layout

```
backend/          FastAPI read API + recommendation-scoring engine (Python)
workers/           Nightly scrapers + SQS ingest pipeline (Python)
frontend/            React SPA (TypeScript)
infra/                 Terraform for every AWS resource
documentation/           Code-overview docs — read these before the code
```

## Local development

Requires Docker, pnpm, and Python 3.11+.

```bash
# Postgres + Redis + backend API on :8000
docker compose up -d postgres redis
cd backend && pip install -e ".[dev]" && alembic upgrade head
docker compose up backend

# Frontend on :5173, talking to the local backend
pnpm install
pnpm --filter frontend dev
```

Run tests/lint for everything:

```bash
pnpm turbo run lint test          # frontend, backend, workers
```

Each app also has its own env file to copy: `backend/.env.example`,
`workers/.env.example`, `frontend/.env.example`.

## Deploying

Nothing here deploys itself. `infra/` is Terraform for the full AWS stack
(Aurora, Redis, SQS, Lambda, API Gateway, CloudFront, and a CodePipeline
that redeploys weekly or on manual trigger — never on every push). See
`documentation/infra.md` for the full apply/bootstrap steps.

## Data pull cadence

Scraping and recommendation generation run nightly via EventBridge,
independent of code deploys. See `documentation/overview.md` for the
schedule.
