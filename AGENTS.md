# AGENTS.md

## Project Overview

Monorepo: `backend/` (Django/DRF) + `frontend/` (Vue 3/Vite). Docker Compose orchestrates everything.

## Commands

### Backend (inside container or locally with venv)

```bash
python manage.py migrate          # apply migrations
python manage.py seed_assets      # seed market assets (idempotent)
python manage.py runserver        # dev server (not used in Docker)
ruff check .                      # lint
ruff check --fix .                # lint + auto-fix
pytest                            # run tests (DJANGO_SETTINGS_MODULE=config.settings)
```

### Market Simulation (root-level shortcuts)

```bash
# Single price update (manual)
./simulate_price.sh SYMBOL PRICE   # e.g., ./simulate_price.sh AAPL 150.00

# Continuous market simulator (realistic price movements)
./simulate_market.sh               # discover and simulate all seeded assets
./simulate_market.sh BR            # discover and simulate assets in BR market only
./simulate_market.sh PETR4 VALE3   # simulate specific symbols repeatedly
./simulate_market.sh --trends AAPL MSFT  # enable per-asset directional trends
```

The simulator runs indefinitely (Ctrl+C to stop). Price fluctuations use a normal distribution (mostly small changes of ±0.3%, occasional larger moves), matching real market behavior. With `--trends`, each asset gets a persistent directional bias to test bull/bear market behavior. Throttles realistically (1–60 sec per symbol based on total count). Use to test price alerts and portfolio updates when markets are closed.

### Frontend (from `frontend/` dir)

```bash
npm install                       # install deps
npm run dev                       # Vite dev server (port 3000)
npm run build                     # typecheck + production build
npm run typecheck                 # vue-tsc --noEmit
npm run lint                      # ESLint (NOTE: uses --ext flag incompatible with ESLint 9 — needs flat config migration)
```

**Always run `npm run typecheck` before considering frontend work done.** The Docker build runs `npm run build` which includes `vue-tsc --noEmit`. Type errors that slip through locally will break the container build.

## Testing

**Always run tests before considering any work done.** Tests catch bugs and verify integration. When tests fail, fix the underlying software issue or update tests to match new requirements.

### Backend Tests

```bash
pytest                             # run all backend tests
pytest alerts/test_views.py -v     # run specific test module
docker compose exec backend pytest  # run tests in container
```

All backend tests must pass: **70/70 tests PASSING** (accounts, alerts, markets, portfolios, trading modules).
- Use `docker compose exec backend pytest` when running in Docker environment
- Test fixtures in `conftest.py` provide `authenticated_client` (DRF APIClient) and model factories
- Mock `realtime.services.publish_event` in tests that trigger async events

### Frontend Unit Tests

```bash
npm run test            # run all unit tests (vitest)
npm run test:ui        # interactive test UI
```

Frontend unit tests use Vitest + Vue Test Utils. Currently have setup issues (Pinia initialization, Vue Router routing) that need fixes for full pass rate. These tests cover component rendering and basic operations.

### Frontend E2E Tests

```bash
npx playwright test     # run end-to-end tests from frontend/
npx playwright test --headed  # run with browser visible
```

Playwright e2E tests in `frontend/e2e/` should verify complete user journeys (auth → portfolio creation → trading → alerts). Currently has configuration issues; fix before considering feature complete.

**Before considering any feature done:**
1. Run backend tests: `docker compose exec backend pytest` — all must pass
2. Run frontend typecheck: `npm run typecheck` — no type errors
3. Run frontend unit tests: `npm run test` — fix or update as needed
4. Run frontend e2e tests: `npx playwright test` — full user journeys must work

If any test fails, investigate and fix the software issue (not the test). Tests are the source of truth.

### Docker

```bash
docker compose up                  # production build (nginx serves frontend)
docker compose up --watch          # dev mode with file watching
docker compose watch               # alternative to up --watch (separate logs)
docker compose build --no-cache frontend   # force rebuild frontend
```

## Architecture

### Backend

- **ASGI entry**: `config.asgi:application` (Channels + Daphne)
- **WSGI fallback**: `config.wsgi:application`
- **Auth**: JWT via `djangorestframework-simplejwt`; access tokens in `localStorage`; refresh on 401 via axios interceptor in `frontend/src/api/client.ts`
- **Realtime**: Channels over Redis (websocket at `/ws/portfolio/`)
- **Celery**: broker at `redis://redis:6379/0`; beat scheduler uses DB backend
- **Error format**: All DRF errors wrapped in `{"error": {...}}` shape (see `config/exceptions.py`)
- **URL convention**: DRF `DefaultRouter` registers views with trailing slashes. Frontend API calls **must** use trailing slashes for DRF routes (e.g., `/api/portfolios/`, `/api/assets/:id/price/`) — mismatched slashes cause auth header drops on redirect or 404s.
- **Settings**: All env vars via `python-decouple` with defaults; see `backend/.env.example`

### Frontend

- **Entry**: `src/main.ts` → `App.vue`; router in `src/router/index.ts`
- **State**: Pinia stores in `src/stores/` (`auth`, `portfolios`, `markets`)
- **API client**: `src/api/client.ts` — axios with `baseURL = '${VITE_API_URL}/api'`; Vite proxy in dev forwards `/api` → `http://backend:8000`
- **Route params**: Views that receive `:id` from routes use `defineProps<{ id?: string | string[] }>()` + `useRoute()` fallback. **Never** assume `props.id` alone is available — always resolve via `route.params.id`. Router has `beforeEnter` guards that validate UUID format and redirect invalid IDs to `/portfolios`.
- **Numeric input**: Use `parseNumericInput()` from `src/utils/numbers.ts` for all user-entered currency/quantity fields before sending to API. Handles BR/US number formats.
- **Path alias**: `@` → `src/`

### Key Bug Patterns (learned the hard way)

1. **`/api/portfolios/undefined/summary/`**: Caused by route param not being passed as component props. Always set `props: true` on `:id` routes **and** add `useRoute()` fallback in the component.
2. **`QuerySet.aggregate()` with non-expression values**: Django's `.aggregate(total=Decimal("0"))` raises `TypeError`. Never pass raw Python values — use `Sum()`, `Count()`, etc.
3. **`publish_event` with f-strings**: `publish_event("portfolio:{portfolio_id}", ...)` was a literal string, not an f-string. Always verify f-string syntax in `realtime/services.py` and `portfolios/services.py`.
4. **Trailing slash mismatches**: DRF DefaultRouter appends `/`. Frontend must match, or Django APPEND_SLASH redirects drop auth headers on POST requests.

### Design Notes (Future Implementation)

**Simulated Price Data Handling**: When price histories are kept (MLP phase), the `AssetQuote` model must distinguish simulated prices from real market data via a flag (e.g., `is_simulated=True`). During market open hours, a scheduled Celery task should delete or exclude simulated entries to prevent corrupting historical charts and analytics. Simulated entries are only intended for offline dev/testing. Details to be fleshed out when price history features are implemented.

## Docker Compose Watch

`develop.watch` is configured for all backend services (`sync+restart` on `./backend`) and frontend (`sync` on `src/`, `index.html`, `vite.config.ts`; `rebuild` on `package.json`).

Current frontend watch mode uses `target: build` (the `npm install` stage of the multi-stage Dockerfile) with `command: npm run dev -- --host 0.0.0.0`. This runs Vite dev server inside the container instead of nginx serving static files.

### Switching to Production Frontend (No HMR)

To run the production nginx build (no watch, no HMR):

1. Remove `target: build` and `command` from the frontend service in `docker-compose.yml`
2. Remove the `develop.watch` block from the frontend service
3. Remove the `volumes` mount for `./frontend/src`
4. Run `docker compose up --build frontend`

### Enabling True Vite HMR (Not Currently Active)

To get browser hot-module-replacement in watch mode:

1. **Vite needs HMR ws accessible from host.** In `vite.config.ts`, add:
   ```ts
   server: {
     hmr: { host: 'localhost', port: 3000 },
   }
   ```
2. **Docker port 3000 must map to the Vite dev server.** Already done (`ports: ["3000:3000"]`).
3. **Vite proxy must target container hostname.** Current config uses `target: 'http://backend:8000'` — this only resolves inside Docker. That's correct for in-container Vite, which is the watch-mode setup.
4. **The `Dockerfile` build stage must have all deps.** The `AS build` stage runs `npm install` then `npm run build`. When `target: build` is used with `command: npm run dev`, the build step runs but the dev server overrides it. This works but rebuilds the production bundle unnecessarily on image build. An alternative is a separate dev Dockerfile or multi-stage target that only installs deps.

## Database Migrations

- All apps have initial migrations (`0001_initial.py`) checked in
- `realtime` and `config` apps have no migrations directory (no models)
- `python manage.py migrate` runs on every backend container start
- `python manage.py seed_assets` also runs on every start (idempotent)

## Market Config

Four markets defined in `config.settings.MARKET_CONFIG`: BR (BRL/BVMF), US (USD/XNYS), UK (GBP/XLON), EU (EUR/XPAR). Fee rates are per-market (BR 0.03%, US 0%, UK/EU 0.1%).