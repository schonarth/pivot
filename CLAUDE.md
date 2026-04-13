# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **Defer to `AGENTS.md`** for the canonical reference on commands, architecture, and known bug patterns. This file adds Claude-specific context on top.

## Commands

### Backend (`backend/` — inside container or local venv)

```bash
python manage.py migrate
python manage.py seed_assets          # idempotent; seed market configs + assets
ruff check .                          # lint
ruff check --fix .                    # lint + auto-fix
pytest                                # all tests
pytest path/to/test_file.py::TestClass::test_method   # single test
pytest -k "test_name_pattern"         # filter by name
```

### Frontend (`frontend/`)

```bash
npm run typecheck   # vue-tsc --noEmit — REQUIRED before considering frontend work done
npm run lint        # ESLint
npm run build       # typecheck + production build (same as Docker build runs)
```

**ESLint 9 note:** `npm run lint` uses `--ext` flag incompatible with ESLint 9. Lint config may need flat config migration.

### Docker

```bash
docker compose up --watch             # dev mode; file watching + Vite dev server in container
docker compose up                     # production build (nginx serves frontend)
docker compose build --no-cache frontend
```

## Architecture

Monorepo: `backend/` (Django 5.2 + DRF) + `frontend/` (Vue 3/Vite). See `AGENTS.md` for the full breakdown.

### Core Event Loop

The primary async cycle that drives the app:

1. **Celery beat** → `fetch_market_prices` (every 5 min) → fetches Yahoo Finance quotes for assets with open positions or active alerts
2. → triggers `evaluate_alerts_for_assets` → checks price conditions, optionally executes auto-trades
3. → `capture_portfolio_snapshots` (every 5 min) → records equity snapshots for TWR calculation
4. → `publish_event(channel, event_type, data)` in `realtime/services.py` → pushes to Channels/Redis → WebSocket clients receive updates

All user-facing actions (trades, deposits, alerts) also call `publish_event` on completion.

### Service Layer

Business logic lives exclusively in `<app>/services.py`. Views call services; models hold no logic. Celery tasks orchestrate multi-step async workflows. This boundary is strict — never add business logic to views or models.

### Django Apps

| App | Purpose |
|-----|---------|
| `accounts` | JWT auth (register/login/logout/me) |
| `markets` | Asset catalog, Yahoo Finance quote fetching, market calendar checks |
| `portfolios` | Portfolio CRUD, cash management, snapshot history, TWR |
| `trading` | Position tracking, trade execution (BUY/SELL with fees + P&L) |
| `alerts` | Price alerts, auto-trade triggers, alert audit trail |
| `timeline` | Activity log (trades, deposits, alert triggers) |
| `realtime` | Channels WebSocket consumer; no models |
| `config` | Settings, ASGI/WSGI, Celery config, exception handler; no models |

### Critical Constraints

- **Single-market portfolios**: each portfolio is locked to one market code (BR/US/UK/EU). Asset market must match portfolio market — enforced in trading and alert views.
- **Fees**: calculated as `gross_value × fee_rate` on both BUY and SELL. Included in BUY average cost; deducted from SELL proceeds for realized P&L.
- **Atomic trades**: `execute_buy/execute_sell` use `select_for_update()` + `atomic()`. Never manipulate Position/Trade/cash outside this pattern.
- **Minimum order value**: 10 (configurable via `MINIMUM_ORDER_VALUE` env var).

### Known Bug Patterns

See `AGENTS.md § Key Bug Patterns` — these are real bugs already encountered:

1. Route param `undefined` in API calls → always use `props: true` **and** `useRoute()` fallback
2. `QuerySet.aggregate()` with raw Python values → use `Sum()`, `Count()`, etc.
3. f-string vs literal string in `publish_event(...)` calls
4. Trailing slash mismatches → POST redirects drop auth headers; always match DRF router's trailing slashes

### Auth

JWT access tokens (15 min) in `localStorage`; refresh tokens (7 days, rotated + blacklisted). Frontend refreshes automatically on 401 via axios interceptor in `src/api/client.ts`. All DRF views require `IsAuthenticated`; all querysets filter by `request.user`.

### Error Format

All API errors come back as `{"error": {...}}` via the custom handler in `config/exceptions.py`.

### WebSocket

`/ws/portfolio/` → `realtime/consumers.py::PortfolioConsumer`. Groups: `user:{user_id}` and `portfolio:{portfolio_id}`. Frontend subscribes by sending `{"action": "subscribe_portfolio", "portfolio_id": "..."}`.

### Frontend Specifics

- Pinia stores: `auth`, `portfolios`, `markets` in `src/stores/`
- API base: `${VITE_API_URL}/api` (dev proxied via Vite to `http://backend:8000`)
- Numeric input: always use `parseNumericInput()` from `src/utils/numbers.ts` for user-entered currency/quantity (handles BR comma vs US dot decimal)
- Path alias: `@` → `src/`

## Environment

All backend env vars via `python-decouple` with defaults. See `backend/.env.example`. Redis slots: 0 = Celery broker, 1 = cache.

Four supported markets: **BR** (BRL/BVMF, 0.03% fee), **US** (USD/XNYS, 0% fee), **UK** (GBP/XLON, 0.1% fee), **EU** (EUR/XPAR, 0.1% fee).
