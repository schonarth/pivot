---
name: Core Event Loop
description: Primary async cycle that drives the app
type: reference
---

# Core Event Loop

The primary async cycle that drives the app:

1. **Celery beat** → `fetch_market_prices` (every 5 min) → fetches Yahoo Finance quotes for assets with open positions or active alerts
2. → triggers `evaluate_alerts_for_assets` → checks price conditions, optionally executes auto-trades
3. → `capture_portfolio_snapshots` (every 5 min) → records equity snapshots for TWR calculation
4. → `publish_event(channel, event_type, data)` in `realtime/services.py` → pushes to Channels/Redis → WebSocket clients receive updates

All user-facing actions (trades, deposits, alerts) also call `publish_event` on completion.
