# Paper Trader Specification

**Version:** 1.0
**Date:** April 8, 2026
**Author:** Gus Schonarth
**Status:** Approved for Development
**Source of truth:** This document refines `PRD-paper-trader.md` into an implementation-ready spec. Where this document is more specific than the PRD, this document wins.

## 1. Scope

### 1.1 MVP scope

The MVP includes:

- Multi-user authentication
- Multi-portfolio paper trading
- One market per portfolio
- Manual BUY/SELL trades
- Periodic delayed price refresh
- Manual portfolio-level and asset-level refresh
- Deposits and withdrawals
- Price alerts
- Optional alert-driven auto-trades
- Portfolio performance that excludes external cash flows
- Portfolio activity/timeline
- Real-time UI updates via WebSocket
- Docker-first local deployment

### 1.2 Explicitly out of MVP scope

The MVP does not include:

- Real-money brokerage integration
- FX conversion or multi-currency portfolios
- Short selling
- Fractional shares
- Options, futures, crypto, ETFs, or mutual funds
- Taxes
- Indicator-based alerts
- AI analysis
- MCP server
- Autonomous strategy engine
- Historical backtesting
- Full service-worker web push infrastructure

### 1.3 MLP scope

The first post-MVP release includes:

- Technical indicators and OHLCV history
- Asset detail charts
- MCP server
- AI-assisted analysis and picks

## 2. Resolved Product Decisions

### 2.1 Portfolio-to-market rule

- Each portfolio belongs to exactly one market: `BR`, `US`, `UK`, or `EU`.
- `portfolio.market` is required.
- `portfolio.base_currency` is derived from `portfolio.market` on the backend and is not user-editable in the frontend.
- A portfolio can only hold assets from its own market.

### 2.2 Authentication model

- Use Django auth from day one.
- Use DRF + JWT for the Vue SPA.
- All API endpoints except health and login/register require authentication.

### 2.3 Quote freshness rule

- Scheduled quotes are delayed and acceptable for MVP.
- Manual trade preview and execution must use the latest cached quote.
- If no cached quote exists, the backend must attempt an on-demand quote refresh before rejecting the trade.
- If the market is closed, the trade may still proceed with the latest available cached quote, even if stale.
- If the market is open and the cached quote is older than the configured refresh interval, the backend must attempt a refresh before executing.

### 2.4 Notification rule

- MVP notification delivery is:
  - in-app notifications in real time
  - browser notifications via the Notification API while the app is open and permission is granted
  - optional email notifications when SMTP is configured
- Full background web push with service workers and VAPID is deferred. Self-hosted HTTPS and public push delivery add operational complexity that is not justified for MVP.

### 2.5 Performance calculation rule

- Absolute trading P&L is always:

`trading_pnl_amount = total_equity - net_external_cash_flows`

- Where:

`net_external_cash_flows = initial_funding + deposits - withdrawals`

- Headline return percentage and comparison charts must use time-weighted return (TWR), not simple `pnl / deposits`, so late deposits do not distort performance.

### 2.6 Auto-trade sizing rule

- Alerts may notify, auto-trade, or do both.
- At least one alert action must be enabled.
- Auto-trade supports either fixed quantity or percentage sizing, never both.
- BUY percentage uses available cash at trigger time.
- SELL percentage uses current position quantity at trigger time.
- Percentage sizing rounds down to a whole share.
- If rounded quantity becomes `0`, the auto-trade is skipped and the alert trigger record must explain why.

### 2.7 Future MCP portfolio identity rule

- When MCP is added, portfolio selection must use explicit portfolio UUIDs, not implicit ordering, display names, or numeric identifiers.

### 2.8 Minimum order value rule

- Minimum order value is `10` units of the portfolio base currency.
- Whole-share quantities only.

### 2.9 Market-hours rule

- Market-hours validation is an exchange-calendar concern, not a frontend string comparison.
- Use IANA time zones and a calendar library with holiday support.
- All backend timestamps are UTC.
- All UI timestamps are rendered in the browser's local timezone.

### 2.10 Event rule

- Internal domain events are published only after the primary database transaction commits successfully.
- Events are for side effects only.
- Core business rules must stay inside explicit service-layer functions and Celery tasks.

## 3. Architecture

### 3.1 Runtime components

- Frontend: Vue 3 + TypeScript + Vite
- Backend API: Django + DRF
- Real-time transport: Django Channels + Redis
- Cache and queue: Redis
- Database: PostgreSQL
- Background work: Celery worker + Celery Beat
- Optional MLP component: MCP server

### 3.2 Backend module boundaries

- `accounts`: authentication, profile, API keys later
- `markets`: market config, calendars, quote provider adapters, symbol resolution
- `portfolios`: portfolio CRUD, summary, performance, snapshots
- `trading`: trade execution, positions, fees, cash ledger
- `alerts`: alert CRUD, evaluation, notification dispatch, auto-trade execution
- `timeline`: portfolio activity feed
- `realtime`: websocket consumers and fan-out

### 3.3 Integration principles

- Yahoo Finance is the primary quote provider for MVP.
- OpenFIGI is optional and used for symbol resolution when an asset is not pre-seeded.
- Seeded assets must cover common symbols for all four supported markets so the app works without OpenFIGI on first boot.

## 4. Data Model

### 4.1 Core entities

#### `users`

- Django auth user model

#### `portfolios`

Required fields:

- `id`
- `user_id`
- `name`
- `market`
- `base_currency`
- `initial_capital`
- `current_cash`
- `is_primary`
- `created_at`
- `updated_at`

Rules:

- `initial_capital >= 0`
- `current_cash >= 0`
- First portfolio for a user is auto-marked `is_primary = true`
- At most one primary portfolio per user
- `base_currency` is always derived from `market`

#### `assets`

Required fields:

- `id`
- `figi` nullable
- `display_symbol`
- `provider_symbol`
- `name`
- `market`
- `exchange`
- `currency`
- `sector` nullable
- `industry` nullable
- `is_seeded`
- `last_symbol_sync_at` nullable
- `created_at`

Rules:

- Unique on `(market, display_symbol)`
- `currency` must match market config

#### `positions`

Required fields:

- `id`
- `portfolio_id`
- `asset_id`
- `quantity`
- `average_cost`
- `created_at`
- `updated_at`

Rules:

- Unique on `(portfolio_id, asset_id)`
- `quantity > 0`
- `average_cost > 0`

#### `trades`

Required fields:

- `id`
- `portfolio_id`
- `asset_id`
- `action`
- `quantity`
- `price`
- `gross_value`
- `fees`
- `net_cash_impact`
- `realized_pnl` nullable
- `rationale`
- `executed_by`
- `executed_at`

Rules:

- `action in ('BUY', 'SELL')`
- `executed_by in ('manual', 'alert', 'autonomous', 'agent')`
- `gross_value = price * quantity`
- For BUY: `net_cash_impact = -(gross_value + fees)`
- For SELL: `net_cash_impact = gross_value - fees`

Note: The PRD uses `total_cost` with different semantics for BUY and SELL. The implementation must replace that ambiguity with `gross_value` and `net_cash_impact`.

#### `cash_transactions`

Required fields:

- `id`
- `portfolio_id`
- `transaction_type`
- `amount`
- `resulting_cash`
- `created_at`

Rules:

- `transaction_type in ('initial_funding', 'deposit', 'withdrawal')`
- `amount > 0`

#### `portfolio_snapshots`

Required fields:

- `id`
- `portfolio_id`
- `cash`
- `positions_value`
- `total_equity`
- `net_external_cash_flows`
- `captured_at`

Purpose:

- performance charts
- TWR calculation
- portfolio history

#### `asset_quotes`

This entity is required for MVP even though the PRD only implies it.

Required fields:

- `id`
- `asset_id`
- `price`
- `currency`
- `source`
- `as_of`
- `fetched_at`
- `is_delayed`
- `provider_payload` JSON nullable

Rules:

- Keep only the latest quote per asset in Redis cache
- Persist the most recent quote row in Postgres for debugging and freshness display

#### `alerts`

Required fields:

- `id`
- `portfolio_id`
- `asset_id`
- `condition_type`
- `threshold`
- `notify_enabled`
- `auto_trade_enabled`
- `auto_trade_side` nullable
- `auto_trade_quantity` nullable
- `auto_trade_pct` nullable
- `status`
- `last_evaluated_at` nullable
- `triggered_at` nullable
- `created_at`
- `updated_at`

Rules:

- `condition_type in ('price_above', 'price_below')`
- `status in ('active', 'triggered', 'paused')`
- at least one of `notify_enabled` or `auto_trade_enabled` must be true
- if `auto_trade_enabled` is true, exactly one of `auto_trade_quantity` or `auto_trade_pct` must be set
- if `auto_trade_enabled` is false, all auto-trade fields must be null

#### `alert_triggers`

Required fields:

- `id`
- `alert_id`
- `triggered_price`
- `triggered_at`
- `outcome`
- `details`
- `notification_sent`
- `trade_id` nullable

`outcome` values:

- `notification_only`
- `notification_and_trade_executed`
- `notification_and_trade_skipped`
- `notification_and_trade_failed`
- `trade_executed`
- `trade_skipped`
- `trade_failed`

#### `timeline_events`

Required fields:

- `id`
- `portfolio_id`
- `event_type`
- `description`
- `metadata` JSON nullable
- `created_at`

### 4.2 Recommended indexes

- `portfolios(user_id)`
- `positions(portfolio_id)`
- `trades(portfolio_id, executed_at desc)`
- `cash_transactions(portfolio_id, created_at desc)`
- `portfolio_snapshots(portfolio_id, captured_at desc)`
- `alerts(portfolio_id, status)`
- `alerts(asset_id, status)`
- `asset_quotes(asset_id, fetched_at desc)`
- `timeline_events(portfolio_id, created_at desc)`

## 5. Business Rules

### 5.1 Portfolio creation

When a user creates a portfolio:

1. Validate `market` is one of the supported markets.
2. Derive `base_currency` from the selected market.
3. Create the portfolio with `current_cash = initial_capital`.
4. Create an `initial_funding` cash transaction.
5. Create an initial portfolio snapshot.
6. Publish `cash_transaction_created`.

### 5.2 Asset lookup

Asset search behavior:

1. Search seeded and previously resolved `assets` rows.
2. If no exact match and OpenFIGI is configured, resolve externally and persist the asset.
3. Do not create duplicate assets for the same `(market, display_symbol)`.
4. Reject assets whose market does not match the target portfolio.

### 5.3 Fee model

MVP brokerage fees:

- BR: `0.03%`
- US: `0.00%`
- UK: `0.10%`
- EU: `0.10%`

Rules:

- Fees are calculated on gross trade value.
- Fees are rounded to 2 decimal places using bankers' rounding or the application's standard decimal policy. The implementation must use one consistent rounding mode everywhere.

### 5.4 BUY execution

Execution flow:

1. Lock the portfolio row with `select_for_update`.
2. Lock the existing position row if present.
3. Validate quantity is a positive integer.
4. Validate the asset belongs to the portfolio market.
5. Validate gross order value is at least the minimum order value.
6. Determine execution price from the latest acceptable quote.
7. Calculate `gross_value`, `fees`, and `net_cash_required`.
8. If insufficient cash, return an error with maximum affordable quantity.
9. Update or create the position.
10. Recompute average cost including buy-side fees.
11. Decrease `current_cash`.
12. Insert trade row with default rationale `Manual operation` when empty.
13. Insert portfolio snapshot.
14. Publish `trade_executed`.

Average cost formula:

`new_average_cost = ((old_average_cost * old_quantity) + gross_value + fees) / new_total_quantity`

### 5.5 SELL execution

Execution flow:

1. Lock portfolio and position rows.
2. Validate quantity is a positive integer.
3. Validate the position exists.
4. Validate position quantity is sufficient.
5. Determine execution price from the latest acceptable quote.
6. Calculate `gross_value`, `fees`, `net_proceeds`, `cost_basis`, and `realized_pnl`.
7. Reduce or delete the position.
8. Increase `current_cash`.
9. Insert trade row.
10. Insert portfolio snapshot.
11. Publish `trade_executed`.

Realized P&L formula:

`realized_pnl = (gross_value - fees) - (average_cost * quantity_sold)`

### 5.6 Cash deposits and withdrawals

Deposit flow:

1. Validate `amount > 0`.
2. Lock portfolio row.
3. Increase `current_cash`.
4. Insert `cash_transactions` row.
5. Insert portfolio snapshot.
6. Publish `cash_transaction_created`.

Withdrawal flow:

1. Validate `amount > 0`.
2. Lock portfolio row.
3. If requested amount exceeds cash, clamp to current cash.
4. Decrease `current_cash`.
5. Insert `cash_transactions` row with the actual withdrawn amount.
6. Insert portfolio snapshot.
7. Publish `cash_transaction_created`.

### 5.7 Quote refresh

Scheduled quote refresh behavior:

1. Build the tracked asset set from:
   - assets in open positions
   - assets referenced by active alerts
2. Group assets by market.
3. Skip markets currently closed.
4. Fetch quotes in batches by market.
5. Write each quote to Redis under `price:{asset_id}`.
6. Upsert latest `asset_quotes` row.
7. Publish `price_refreshed` for each updated asset.
8. After quote writes complete, enqueue alert evaluation for only the assets refreshed in this run.

Manual refresh behavior:

- Portfolio refresh updates all assets in that portfolio.
- Asset refresh updates one asset.
- Manual refresh may run outside market hours. If the provider returns no new data, the API returns the existing latest quote and marks it stale.

### 5.8 Alert evaluation

Rules:

- Alerts are one-shot.
- Only `active` alerts are evaluated.
- Scheduled alert evaluation only runs after a fresh quote update.
- A triggered alert moves to `triggered` immediately inside the same transaction that records the trigger.
- Paused alerts are ignored.
- Notifications are sent when `notify_enabled = true`.
- Auto-trades are attempted when `auto_trade_enabled = true`.
- Auto-trade does not implicitly enable notifications.

Evaluation flow:

1. Load active alerts for refreshed assets.
2. Lock each candidate alert row before acting on it.
3. Evaluate `price_above` or `price_below` against the fresh quote.
4. If not matched, update `last_evaluated_at` and stop.
5. If matched, prepare both side effects independently: notification if enabled, auto-trade if enabled.
6. If auto-trade is enabled, compute quantity, attempt trade execution, and capture whether it executed, was skipped, or failed.
7. Create one `alert_triggers` row summarizing the full trigger outcome, including notification and trade results.
8. Mark the alert as `triggered`.
9. Publish `alert_triggered`.

Auto-trade rationale format:

`Auto-trade triggered by alert: {condition_type} {threshold}`

### 5.9 Timeline generation

Timeline entries are generated from domain events, not from controller code.

Required event mappings:

- `trade_executed` -> trade timeline entry
- `cash_transaction_created` -> deposit/withdrawal timeline entry
- `alert_triggered` -> alert timeline entry
- `price_refreshed` does not create timeline noise by default

### 5.10 Performance and valuation

Definitions:

- `positions_value = sum(position.quantity * latest_quote_price)`
- `total_equity = current_cash + positions_value`
- `net_external_cash_flows = sum(initial_funding + deposits - withdrawals)`
- `trading_pnl_amount = total_equity - net_external_cash_flows`

Time-weighted return:

For each snapshot interval:

`period_return = (ending_equity - starting_equity - external_flow_during_period) / starting_equity`

Portfolio return over multiple periods:

`twr = product(1 + period_return) - 1`

Rules:

- If there is no prior snapshot, return percentage is `0`.
- If starting equity is `0`, skip percentage calculation for that interval.

## 6. API Specification

### 6.1 Response conventions

- JSON only
- UTC timestamps in ISO 8601
- Currency amounts serialized as strings to avoid float drift
- Paginated list endpoints use cursor or page-number pagination consistently across the API
- Error format:

```json
{
  "error": {
    "code": "insufficient_cash",
    "message": "Insufficient cash. You have 1000.00, but this trade requires 4850.29.",
    "details": {
      "available_cash": "1000.00",
      "required_cash": "4850.29",
      "max_quantity": 20
    }
  }
}
```

### 6.2 Auth endpoints

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`

### 6.3 Portfolio endpoints

- `GET /api/portfolios`
- `POST /api/portfolios`
- `GET /api/portfolios/{id}`
- `PUT /api/portfolios/{id}`
- `DELETE /api/portfolios/{id}`
- `GET /api/portfolios/{id}/summary`
- `GET /api/portfolios/{id}/performance`
- `POST /api/portfolios/{id}/refresh-prices`
- `POST /api/portfolios/{id}/deposit`
- `POST /api/portfolios/{id}/withdraw`
- `GET /api/portfolios/{id}/cash-transactions`
- `GET /api/portfolios/{id}/timeline`

`POST /api/portfolios` request body:

```json
{
  "name": "My BR Portfolio",
  "market": "BR",
  "initial_capital": "10000.00"
}
```

### 6.4 Position endpoints

- `GET /api/portfolios/{id}/positions`
- `GET /api/portfolios/{id}/positions/{asset_id}`

Position payload fields:

- asset metadata
- quantity
- average_cost
- current_price
- current_price_as_of
- unrealized_pnl_amount
- unrealized_pnl_pct
- market
- currency

### 6.5 Trade endpoints

- `POST /api/portfolios/{id}/trades`
- `GET /api/portfolios/{id}/trades`
- `GET /api/trades/{id}`

Trade request body:

```json
{
  "asset_id": "uuid",
  "action": "BUY",
  "quantity": 20,
  "rationale": "Buying the dip"
}
```

Trade response payload must include:

- executed trade
- updated cash
- updated position summary if relevant
- latest portfolio summary

### 6.6 Asset endpoints

- `GET /api/assets?q=PETR&market=BR`
- `GET /api/assets/{symbol}?market=BR`
- `GET /api/assets/{symbol}/price?market=BR`
- `POST /api/assets/{symbol}/refresh-price?market=BR`

For MVP, asset detail is quote-centric. OHLCV and indicators are added in MLP.

### 6.7 Alert endpoints

- `GET /api/portfolios/{id}/alerts`
- `POST /api/portfolios/{id}/alerts`
- `PUT /api/alerts/{id}`
- `DELETE /api/alerts/{id}`
- `POST /api/alerts/{id}/pause`
- `POST /api/alerts/{id}/resume`

Alert create payload examples:

```json
{
  "asset_id": "uuid",
  "condition_type": "price_below",
  "threshold": "42.00",
  "notify_enabled": true,
  "auto_trade_enabled": false
}
```

```json
{
  "asset_id": "uuid",
  "condition_type": "price_below",
  "threshold": "42.00",
  "notify_enabled": true,
  "auto_trade_enabled": true,
  "auto_trade_side": "BUY",
  "auto_trade_quantity": 20
}
```

### 6.8 System endpoints

- `GET /api/health`
- `GET /api/markets/status`
- `GET /api/system/stats`

## 7. WebSocket Specification

### 7.1 Channels

The backend must avoid a single global public price channel.

Required groups:

- `user:{user_id}` for user-scoped notifications
- `portfolio:{portfolio_id}` for portfolio summary, timeline, and position updates

### 7.2 Event types

- `price.updated`
- `portfolio.updated`
- `trade.executed`
- `alert.triggered`
- `cash.updated`
- `notification.created`

### 7.3 Frontend behavior

- Reconnect automatically with exponential backoff.
- If WebSocket is unavailable, fall back to polling every `WEBSOCKET_FALLBACK_POLLING` seconds.
- Show stale-data indicators when quote freshness exceeds the configured interval during market hours.

## 8. Frontend Specification

### 8.1 Required routes for MVP

- `/`
- `/login`
- `/register`
- `/portfolios`
- `/portfolios/new`
- `/portfolios/:id`
- `/portfolios/:id/trades`
- `/portfolios/:id/trades/new`
- `/portfolios/:id/alerts`
- `/assets`
- `/assets/:symbol`
- `/settings`

### 8.2 Dashboard

The main dashboard must show:

- portfolio cards for all user portfolios
- total equity
- cash
- invested value
- trading P&L amount
- trading return percentage
- net deposits/withdrawals
- latest activity
- market-open/closed status badges

### 8.3 Portfolio detail page

The portfolio page must include:

- summary header
- positions table
- cash balance
- net external cash flow summary
- last successful refresh timestamp
- `Refresh Prices` action
- `Deposit` action
- `Withdraw` action
- `New Trade` action
- recent timeline entries
- alerts summary

### 8.4 Trade form

The form must:

- search assets within the portfolio market
- show latest price and quote timestamp
- show fee preview
- show gross and net cash impact preview
- warn when market is closed
- require explicit confirmation for closed-market trades
- show actionable validation errors

### 8.5 Alerts page

The page must:

- list alerts grouped by status
- show asset, condition, threshold, action, trigger time, and latest outcome
- allow create, edit, pause, resume, delete
- reveal auto-trade inputs only when auto-trade is selected

### 8.6 Asset page

For MVP the asset page must show:

- asset identity fields
- current price
- quote freshness
- market status
- `Refresh Price` action
- quick actions to trade or create alert

### 8.7 Accessibility and responsiveness

- Keyboard navigation for all forms and dialogs
- Visible focus states
- Mobile layouts for portfolio summary, positions, and alerts
- Dark mode supported from MVP

## 9. Background Jobs

### 9.1 Required Celery tasks for MVP

- `fetch_market_prices`
- `evaluate_alerts_for_assets`
- `capture_portfolio_snapshots`
- `send_email_notification` when SMTP configured

### 9.2 Scheduling rules

- Quote fetch interval is configurable: `300`, `900`, `1800`, `3600` seconds
- Default is `300`
- Quote fetch runs only for markets currently open
- Snapshot capture runs at least once per quote cycle for portfolios touched by updated assets, and also after each trade or cash transaction

### 9.3 Failure handling

- Quote fetch failures must not delete the last known quote.
- Partial quote fetch success is acceptable.
- Alert evaluation failures for one alert must not block others.
- Task retries must use bounded exponential backoff.

## 10. Security and Reliability Requirements

### 10.1 Authorization

- Every portfolio-scoped read and write must verify ownership.
- Asset lookups are public only after auth in MVP.
- MLP API keys are stored hashed, never plaintext after creation.

### 10.2 Validation

- Server-side validation is authoritative.
- Decimal math must use `Decimal`, never float.
- Market and currency mismatches are hard errors.

### 10.3 Rate limits

- Default authenticated API throttle: `100 requests/minute/user`
- Manual refresh endpoints need tighter throttles to protect Yahoo Finance.
- Frontend keeps the manual refresh button disabled for `3` seconds after each click.
- Backend applies a `30` second resource-scoped cooldown per user:
  - portfolio refresh keyed by `(user_id, portfolio_id)`
  - asset refresh keyed by `(user_id, asset_id)`
- Repeated manual refresh calls during the cooldown must not trigger a new provider request.
- During cooldown, the backend should return the latest known refresh result and quote freshness metadata rather than a hard error.

### 10.4 Observability

- Structured logs for trades, alerts, quote refresh, and task failures
- Health endpoint checks database, Redis, and worker heartbeat status
- Sentry is optional and initializes only when credentials are provided through `docker-compose.yml` or `.env`, depending on deployment style

## 11. MVP Acceptance Checklist

### 11.1 Portfolio and cash

- User can register, log in, and create multiple portfolios.
- Each portfolio is bound to one market and one currency.
- Deposits and withdrawals update cash immediately.
- Withdrawals clamp at zero cash with explicit warning.

### 11.2 Trading

- User can buy and sell whole shares.
- Fee preview matches execution.
- Average cost includes buy-side fees.
- Realized P&L is stored on sell trades.
- Closed-market manual trades require confirmation and use the last known quote.

### 11.3 Prices and valuation

- Scheduled prices refresh during market hours only.
- Manual portfolio refresh updates all portfolio assets.
- Manual asset refresh updates one asset.
- Portfolio totals update in real time without full page reload.

### 11.4 Alerts

- User can create notify and auto-trade alerts.
- Alerts trigger only once.
- Notify alerts create in-app notifications.
- Auto-trade alerts execute with the fresh triggering quote when possible.
- Trigger outcomes are visible in UI history.

### 11.5 Performance

- Dashboard and portfolio pages show absolute trading P&L, return percentage, and net deposits/withdrawals separately.
- Return percentage excludes external cash-flow distortion via TWR.

## 12. Delivery Sequence

Recommended implementation order:

1. Project scaffolding, auth, market config, seeded assets
2. Portfolio CRUD and cash ledger
3. Trade engine and positions
4. Quote provider adapter, quote cache, manual refresh
5. WebSocket updates and portfolio summary refresh
6. Snapshots and performance calculations
7. Alerts and auto-trade
8. Timeline and notifications
9. UI polish, dark mode, responsive fixes, documentation

## 13. Open Gaps and Follow-Ups

These items should be confirmed before implementation starts, but they are not blockers for drafting the architecture.

### 13.1 Asset universe size

- Do not lock the project to a fixed hand-curated seed list up front.
- Initial coverage target for MVP: approximately top `100` assets per market, obtained through lightweight market research during development.
- Initial coverage target for MLP: expand toward approximately top `500` assets per market.
- Seed data may be generated from the running app and persisted back into the project as the development dataset matures.

### 13.2 Quote provider fallback

- The adapter boundary should support multiple quote providers from the start.
- Secondary providers may be added in advance without committing to a strict priority order yet.
- Provider quality and fallback order can be refined later from implementation experience.

### 13.3 Email provider expectations

- SMTP is optional, but there is no decision on whether failed email delivery should be visible in UI. Recommendation: log failures and expose them only in admin/system stats for MVP.

### 13.4 Portfolio deletion semantics

- The PRD includes delete endpoints but does not define whether deleting a portfolio with history is allowed.
- Recommendation: allow deletion in MVP because this is paper data only, but require an explicit confirmation step in the UI.

### 13.5 Web notification wording

- If true background push is required later, it should be specified separately from foreground Notification API support.

### 13.6 Performance chart granularity

- Snapshot frequency for long-range charts is not explicitly defined. Recommendation: use event-driven snapshots plus one snapshot per quote cycle, then downsample in the API response.

### 13.7 Exchange holiday source

- The PRD defines market hours but not the holiday-calendar source. Recommendation: choose one maintained Python calendar library during implementation and use it consistently across all markets.
