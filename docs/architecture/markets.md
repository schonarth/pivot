---
name: Market Configuration
description: Supported markets and their characteristics
type: reference
---

# Supported Markets

Four supported markets, each with currency and fee configuration:

| Market | Code | Currency | Exchange | Fee |
|--------|------|----------|----------|-----|
| Brazil | BR | BRL | BVMF | 0.03% |
| US | US | USD | XNYS | 0% |
| UK | UK | GBP | XLON | 0.1% |
| EU | EU | EUR | XPAR | 0.1% |

## Environment Variables

All configuration via `python-decouple` with defaults in `backend/.env.example`.

## Redis Slots

- Slot 0: Celery broker
- Slot 1: Cache
