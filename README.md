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
cd backend && pip install -e ".[dev]" && cd ..
pnpm migrate                        # applies migrations -- needs Postgres up first

pnpm dev
```

`pnpm dev` brings up every `docker-compose.yml` service (Postgres, Redis,
LocalStack, backend API on `:8000`, `workers`) via `docker compose up
--build`, and the frontend's Vite dev server on `:3000`, in one terminal
with merged/labeled output (`concurrently` — Ctrl+C stops both). `pnpm
migrate` only needs to run once against a fresh Postgres volume (start it
with `docker compose up -d postgres` first if `pnpm dev` isn't already
running), same as running the backend any other way.

- `pnpm migrate` — `alembic upgrade head` against whatever `DATABASE_URL`
  resolves to (needs `backend`'s Python deps installed, same as above).
- `pnpm migrate:gen -m "add foo column"` — generates a new migration with
  the next sequential revision id and commits it (see
  `documentation/backend.md`). Fill in `upgrade()`/`downgrade()` before
  running `pnpm migrate` — this repo hand-writes migration bodies, it
  doesn't `--autogenerate` them.

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

A `pnpm install` also sets up a git pre-commit hook (husky + lint-staged)
that runs `prettier --write` on staged `.ts`/`.tsx`/`.md`/`.json`/`.yml`
files, so formatting drift never reaches a commit in the first place —
`pnpm format`/`pnpm format:check` cover the whole tree on demand instead
of just staged files.

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

Nothing here deploys itself — no push, PR merge, or git hook ever
touches real AWS. `infra/` is Terraform for the full AWS stack (Aurora,
Redis, SQS, Lambda, API Gateway, CloudFront, and a CodePipeline that
redeploys weekly or on manual trigger). See `documentation/infra.md` for
the full apply/bootstrap steps. Root `package.json` scripts cover the two
things you'll actually run by hand, from anywhere in the repo (no `cd`
needed):

- **Shipped an app-code fix (backend/workers/frontend), no `infra/`
  changes?** `pnpm deploy` is the only command you need — it starts the
  CodePipeline, which builds fresh images, runs `alembic upgrade head`
  against Aurora as part of its own build (see
  `infra/codebuild/buildspec.yml`), and deploys. `pnpm deploy:status`
  checks progress.
- **Changed something under `infra/`?** `pnpm infra:plan` /
  `pnpm infra:apply` (still prompts for confirmation — never
  `-auto-approve`, this touches real infrastructure) /
  `pnpm infra:output` for the Terraform outputs referenced throughout
  these docs (e.g. `db_bastion_instance_id`).

`pnpm migrate` / `pnpm migrate:gen` (see above) are for local dev only —
they don't touch production, which gets migrated by the pipeline itself.

## Data pull cadence

Scraping and recommendation generation run nightly via EventBridge,
independent of code deploys. See `documentation/overview.md` for the
schedule.
