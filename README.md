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
pnpm install
cd backend && pip install -e ".[dev]" && alembic upgrade head && cd ..   # once, before the first run

pnpm dev
```

`pnpm dev` brings up every `docker-compose.yml` service (Postgres, Redis,
LocalStack, backend API on `:8000`, `workers`) via `docker compose up
--build`, and the frontend's Vite dev server on `:3000`, in one terminal
with merged/labeled output (`concurrently` — Ctrl+C stops both). The
`alembic upgrade head` step only needs to run once against a fresh
Postgres volume, same as running the backend any other way.

To run pieces individually instead (e.g. you don't need the frontend, or
want backend logs separate from everything else), start services by name:
`docker compose up -d postgres redis` /
`docker compose up backend` / `pnpm --filter frontend dev`, etc.

Run tests/lint for everything:

```bash
pnpm turbo run lint test          # frontend, backend, workers
```

Each app also has its own env file to copy: `backend/.env.example`,
`workers/.env.example`, `frontend/.env.example`.

### Running `workers` locally (LocalStack)

`workers` talks to real SQS in AWS; locally it talks to
[LocalStack](https://localstack.cloud) instead, so the full
scrape → enqueue → poll → canonicalize pipeline is testable without
touching real AWS or spending anything:

```bash
docker compose up -d postgres localstack
docker compose up -d --build workers

# Scrape + enqueue (see documentation/workers.md for the free-source caveats)
docker compose exec workers python local/run_nightly_scrape.py

# In another terminal: drain the queue the same way the real SQS-triggered
# Lambda would (leave running while you scrape)
docker compose exec workers python local/poll_queue.py
```

See `documentation/workers.md`'s "Running locally against LocalStack"
section for details.

## Deploying

Nothing here deploys itself. `infra/` is Terraform for the full AWS stack
(Aurora, Redis, SQS, Lambda, API Gateway, CloudFront, and a CodePipeline
that redeploys weekly or on manual trigger — never on every push). See
`documentation/infra.md` for the full apply/bootstrap steps.

## Data pull cadence

Scraping and recommendation generation run nightly via EventBridge,
independent of code deploys. See `documentation/overview.md` for the
schedule.
