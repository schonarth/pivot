---
name: Critical Constraints
description: Architectural invariants that must be maintained
type: reference
---

# Critical Constraints

- **Single-market portfolios**: each portfolio is locked to one market code (BR/US/UK/EU). Asset market must match portfolio market — enforced in trading and alert views.
- **Fees**: calculated as `gross_value × fee_rate` on both BUY and SELL. Included in BUY average cost; deducted from SELL proceeds for realized P&L.
- **Atomic trades**: `execute_buy/execute_sell` use `select_for_update()` + `atomic()`. Never manipulate Position/Trade/cash outside this pattern.
- **Minimum order value**: 10 (configurable via `MINIMUM_ORDER_VALUE` env var).
- **Service layer isolation**: Business logic lives exclusively in `<app>/services.py`. Views call services; models hold no logic. Celery tasks orchestrate multi-step async workflows. This boundary is strict — never add business logic to views or models.
