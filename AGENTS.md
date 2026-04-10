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

### Frontend (from `frontend/` dir)

```bash
npm install                       # install deps
npm run dev                       # Vite dev server (port 3000)
npm run build                     # typecheck + production build
npm run typecheck                 # vue-tsc --noEmit
npm run lint                      # ESLint (NOTE: uses --ext flag incompatible with ESLint 9 — needs flat config migration)
```

**Always run `npm run typecheck` before considering frontend work done.** The Docker build runs `npm run build` which includes `vue-tsc --noEmit`. Type errors that slip through locally will break the container build.

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