# frontend/

Vite + React + TypeScript single-page app that reads from the backend
API. No authentication or billing yet — the API layer is isolated from
the UI (`src/api/`) specifically so those can be added later without
touching component code.

## Layout

```
frontend/src/
  api/
    client.ts             apiGet<T>()/apiPost<T>() fetch wrappers (base URL from VITE_API_BASE_URL)
    types.ts               TypeScript mirrors of the backend's Pydantic schemas
    politicians.ts, trades.ts, recommendations.ts   Typed fetch functions per resource
  hooks/
    useAsyncData.ts         Generic loading/error/data hook
    usePoliticians.ts, useTrades.ts, useRecommendations.ts, useRecommendationDetail.ts   Thin wrappers over useAsyncData
  components/
    Layout.tsx               Header + nav
    RecommendationCard.tsx    One recommendation, links to its detail page
    TradeTable.tsx             Canonical trade list
    SimulatedOrderForm.tsx      Order preview/confirm form (see below)
  pages/
    Dashboard.tsx              "/" — recommendation feed
    RecommendationDetail.tsx    "/recommendations/:id" — scoring breakdown + simulate-trade UI
    Trades.tsx                  "/trades" — filterable trade table
  App.tsx                       Route definitions
  main.tsx                       Entry point
  styles/global.css               Plain CSS, dark theme
```

## API layer (`src/api/`)

`client.ts` exports `apiGet<T>(path, params?)` and `apiPost<T>(path, body)`,
which build off `VITE_API_BASE_URL` (default `http://localhost:8000/api/v1`)
and throw `ApiError` on a non-2xx response. `recommendations.ts`,
`trades.ts`, and `politicians.ts` each export one typed function per
backend route (`fetchRecommendations`, `fetchRecommendationDetail`,
`submitSimulatedOrder`, `fetchTrades`, `fetchPoliticians`). `types.ts` is
a hand-maintained mirror of the backend's `schemas/` — keep the two in
sync when a field changes.

## Data hooks (`src/hooks/`)

`useAsyncData(fetcher, deps)` runs `fetcher()` whenever `deps` changes,
tracks `{ data, error, loading }`, and cancels stale updates if the
component unmounts or `deps` changes again before the request resolves.
The resource-specific hooks (`useRecommendations`, `useTrades`,
`usePoliticians`, `useRecommendationDetail`) just bind this to one API
function. `useRecommendationDetail(id, refreshKey)` takes an extra
`refreshKey` so a caller can force a refetch (e.g. after logging a
simulated order) by bumping it as a plain `useState` counter.

## Pages

- **`Dashboard`** (`/`) — calls `useRecommendations()` with no ticker
  filter, renders one `RecommendationCard` per result.
- **`RecommendationDetail`** (`/recommendations/:id`) — the scoring
  breakdown and supporting trades from `GET /recommendations/{id}`, plus
  `SimulatedOrderForm` for logging a paper trade and a table of past
  simulated orders for this recommendation. No real brokerage is called;
  see `documentation/backend.md`'s "Simulated trade logging" section.
- **`Trades`** (`/trades`) — a ticker text input drives `useTrades({ ticker })`,
  rendered as a `TradeTable`.

## Build/test tooling

- `pnpm dev` (this package) — Vite dev server on port 3000. The root
  `pnpm dev` (see root `package.json`) runs this alongside
  `docker compose up --build` for the full local stack in one command.
- `pnpm build` — `tsc -b && vite build`, output to `dist/`.
- `pnpm lint` — ESLint flat config (`eslint.config.js`): TypeScript,
  React Hooks, and React Refresh rules.
- `pnpm test` — Vitest + Testing Library (`jsdom` environment,
  `src/setupTests.ts` registers `@testing-library/jest-dom` matchers and
  an `afterEach(cleanup)`).
