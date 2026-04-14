---
name: WebSocket Architecture
description: Real-time updates via Channels and WebSocket
type: reference
---

# WebSocket Architecture

## Endpoint & Consumer

- Endpoint: `/ws/portfolio/` → `realtime/consumers.py::PortfolioConsumer`

## Groups

- `user:{user_id}` - all portfolios for a user
- `portfolio:{portfolio_id}` - specific portfolio

## Frontend Subscription

Frontend subscribes by sending:
```json
{"action": "subscribe_portfolio", "portfolio_id": "..."}
```

## Publishing Events

Services call `publish_event(channel, event_type, data)` in `realtime/services.py` to push updates to connected clients.
