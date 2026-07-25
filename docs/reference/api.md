# API Reference (Source of Truth)

All endpoints use `application/json`. Monetary values are strings with two decimals and IDs are UUIDs unless noted. JWT auth uses `Authorization: Bearer <token>`; `/auth/register`, `/auth/login`, and `/mcp/token/exchange/` are public.

## Authentication (`/api/auth/`)

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| POST | `/api/auth/register` | None | Register; body: `{email, password}`; returns user and JWT tokens. |
| POST | `/api/auth/login` | None | Login; body: `{email, password}`; returns JWT tokens. |
| POST | `/api/auth/logout` | JWT | Blacklist refresh token; body: `{refresh}`. |
| GET | `/api/auth/me` | JWT | Current user profile, including `api_uuid`. |
| POST | `/api/auth/token/refresh` | None | Refresh access token; body: `{refresh}`; returns new `access`. |

## Portfolios (`/api/portfolios/`)

| Method | Endpoint | Purpose |
|---|---|---|
| GET/POST | `/api/portfolios/` | List user portfolios or create one; create body: `{name, market, initial_capital}`, where `market` is BR, US, UK, or EU. |
| GET/PUT/PATCH/DELETE | `/api/portfolios/{id}/` | Retrieve, update, or delete a portfolio. |
| GET | `/api/portfolios/{id}/summary/` | Cash, positions, `positions_value`, total equity, trading P&L, and net flows. |
| GET | `/api/portfolios/{id}/performance/` | TWR and historical snapshots. |
| POST | `/api/portfolios/{id}/deposit` | Deposit cash; body: `{amount}`; returns transaction and updated cash. |
| POST | `/api/portfolios/{id}/withdraw` | Withdraw cash; body: `{amount}`; returns transaction, updated cash, and an optional clamp warning. |
| POST | `/api/portfolios/{id}/refresh_prices` | Refresh position quotes; returns refreshed count. |
| GET | `/api/portfolios/{id}/cash_transactions/` | List deposits and withdrawals. |
| GET | `/api/portfolios/{id}/timeline/` | List activity, including trades, alert triggers, and deposits. |

## Positions and Trades

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/portfolios/{portfolio_id}/positions/` | List positions. |
| GET | `/api/portfolios/{portfolio_id}/positions/{asset_id}/` | Position detail: quantity, average cost, current price, unrealized P&L, and related values. |
| GET/POST | `/api/portfolios/{portfolio_id}/trades/` | List or execute trades; POST body: `{asset_id, action, quantity, rationale?}`. |
| GET | `/api/trades/{id}/` | Trade detail. |

`action` is `BUY` or `SELL` (case-insensitive). Trade creation returns `trade`, `cash`, `summary`, and optionally `position`.

## Assets and Markets

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/assets/` | List seeded assets; filter with `?market=BR` or search with `?q=PETR`. |
| GET | `/api/assets/{id}/` | Asset detail. |
| GET | `/api/assets/{id}/price/` | Latest quote: `price`, `currency`, `source`, `as_of`, `is_delayed`, and `market_open`. |
| POST | `/api/assets/{id}/refresh-price/` | Refresh a Yahoo Finance quote or return `stale=true` on failure. |
| GET | `/api/markets/` | List market configurations. |
| GET | `/api/markets/{id}/` | Market configuration detail, including fees, currency, exchange, and timezone. |
| GET | `/api/markets/status` | Open/closed status by market; returns `{BR: {open: bool}, US: {...}, ...}`. |

## Alerts

| Method | Endpoint | Purpose |
|---|---|---|
| GET/POST | `/api/portfolios/{portfolio_id}/alerts/` | List or create alerts; POST body: `{asset_id, condition (ABOVE/BELOW), target_price, should_auto_trade?, action?, quantity?}`. |
| GET/PUT/PATCH/DELETE | `/api/alerts/{id}/` | Retrieve, update, or delete an alert. |
| POST | `/api/alerts/{id}/pause/` | Pause an alert. |
| POST | `/api/alerts/{id}/resume/` | Resume an alert. |
| GET | `/api/alert-triggers/` | List trigger history. |

`condition` is `ABOVE` or `BELOW`.

## MCP (`/api/mcp/`)

Agent-facing endpoints use an OTP-exchanged `agent_token` parameter in the request body or query string.

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| POST | `/api/mcp/otp/generate/` | JWT | Generate a 60-second OTP; returns `{code, expires_at}`. |
| POST | `/api/mcp/token/exchange/` | OTP | Exchange `{user_id (api_uuid), otp, name?, origin?}` for an agent token; returns `{token}`. |
| GET | `/api/mcp/agents/` | JWT | List authenticated agents. |
| DELETE | `/api/mcp/agents/{agent_id}/` | JWT | Revoke agent token. |
| POST | `/api/mcp/asset-insight/` | Agent | Cached (24-hour) AI insight: summary, technical analysis, sentiment, and recommendation; body: `{agent_token, asset_id}`. |
| GET | `/api/mcp/ai-settings/` | Agent | Read-only monthly budget, usage, and remaining-budget information; no API key is exposed. |
| GET | `/api/mcp/strategy-rules/` | Agent | Strategy rule list; pass `agent_token` in the query string. |
| GET | `/api/mcp/strategy-instances/` | Agent | Strategy instance list; pass `agent_token` in the query string. |
| GET | `/api/mcp/strategy-trades/` | Agent | Strategy trade list; pass `agent_token` in the query string. |
| POST | `/api/mcp/backtest/create/` | Agent | Create backtest; body: `{agent_token, strategy_instance_id, date_from, date_to}`; returns backtest object. |
| GET | `/api/mcp/backtest/{id}/results/` | Agent | Backtest results; pass `agent_token` in the query string. |
| GET | `/api/mcp/agent-trades/` | Agent | Agent-executed trades; pass `agent_token` in the query string. |
| GET | `/api/mcp/schema/` | None | Endpoint schema and auth/caching strategies. |

## Health and System

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Service health; returns `{status: ok}`. |
| GET | `/api/system/stats` | Uptime and memory statistics. |

## Field Naming

Requests currently use `asset_id` for trades and alerts. Responses use `asset` plus `asset_display_symbol`, `asset_name`, `asset_market`, and `asset_currency`. The planned standard is `asset` for request bodies as well, affecting trade and alert creation.
