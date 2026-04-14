---
name: Django Apps Reference
description: Purpose and responsibility of each Django app in the system
type: reference
---

# Django Apps

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
