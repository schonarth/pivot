---
status: complete
priority: p2
issue_id: "011"
tags: [portfolio-summary, django-orm, query-observability, n-plus-one, performance]
dependencies: []
---

# Bulk Load Portfolio Summary Quotes

## Problem Statement

`GET /api/portfolios/{id}/summary/` can repeat latest-quote lookups for each position and watch asset. Query observability surfaced portfolio summary endpoints as follow-up query-heavy candidates after the discovery hotspot was fixed.

This matters because portfolio summary is a common dashboard/detail-page endpoint and query count should scale with data groups, not one latest-quote query per asset.

## Findings

- `backend/portfolios/services.py::get_portfolio_summary()` loops portfolio positions and calls `get_latest_quote(str(pos.asset_id))` for each position.
- The same function loops watch memberships and calls `get_latest_quote(str(membership.asset_id))` for each watch asset.
- Positions and watch memberships already use `select_related("asset")`, so asset metadata access is not the likely hotspot.
- The likely repeated pattern is latest quote lookup per asset across positions and watch assets.

## Proposed Solutions

### Option 1: Bulk Load Latest Quotes in Portfolio Summary

**Approach:** Gather position and watch asset IDs, bulk-load quotes ordered by `asset_id`, `-fetched_at`, then reuse a dictionary in both loops.

**Pros:**
- Small, localized change
- Preserves response shape and summary semantics
- Easy to cover with a query-count regression test

**Cons:**
- Duplicates a latest-quote grouping pattern unless a shared helper already exists or is added later

**Effort:** 1-2 hours

**Risk:** Low

---

### Option 2: Add Shared Bulk Latest Quote Helper

**Approach:** Add a helper near existing quote lookup code that accepts asset IDs and returns latest quotes by asset ID, then use it from portfolio summary and future endpoints.

**Pros:**
- Reusable for discovery, summaries, and other quote-heavy endpoints
- Centralizes latest-quote ordering rules

**Cons:**
- Slightly broader abstraction
- Requires checking existing quote-provider boundaries before adding it

**Effort:** 2-3 hours

**Risk:** Medium

## Recommended Action

Add a shared latest-quotes helper in `backend/markets/quote_provider.py`, use it from `get_portfolio_summary()`, and cover the summary endpoint with a query-count regression test.

## Technical Details

Affected files:
- `backend/portfolios/services.py` - `get_portfolio_summary()`
- `backend/portfolios/test_views.py` or a service-level test module - regression coverage
- possible helper location: `backend/markets/quote_provider.py` or `backend/markets/services.py`

Database changes:
- None expected.

## Resources

- Related observability ADR: `docs/adrs/ADR-008-global-in-memory-query-observability.md`
- Related solved pattern: `docs/solutions/discovery-query-inputs-bulk-loaded-20260424.md`

## Acceptance Criteria

- [x] Portfolio summary response payload remains unchanged
- [x] Latest quote lookup is bulk-loaded for positions and watch assets
- [x] Regression test proves query count does not grow by one latest-quote query per asset
- [x] Targeted portfolio tests pass
- [x] Query observability concern addressed by query-count regression

## Work Log

### 2026-05-07 - Initial Discovery

**By:** Codex

**Actions:**
- Reviewed query observability follow-up candidates after PR #40.
- Inspected `get_portfolio_summary()` and identified per-position/per-watch latest quote calls.
- Queued this todo after the higher-priority `GET /api/ai/get_settings/` serializer lookup issue.

**Learnings:**
- Portfolio summary already avoids asset metadata N+1 through `select_related("asset")`.
- Latest quote lookup is the most likely remaining query-scaling problem.

### 2026-05-07 - Implementation

**By:** Codex

**Actions:**
- Added `get_latest_quotes(asset_ids)` to `backend/markets/quote_provider.py`.
- Updated `get_portfolio_summary()` to bulk-load quotes for positions and watch memberships.
- Added `test_portfolio_summary_bulk_loads_latest_quotes`.
- Ran `docker compose exec backend pytest portfolios/test_views.py::TestPortfolioEndpoints::test_portfolio_summary_bulk_loads_latest_quotes -q`.
- Ran `docker compose exec backend pytest portfolios/test_views.py -q`.
- Ran `docker compose exec backend pytest -q`.
- Ran `docker compose exec backend ruff check portfolios/test_views.py markets/quote_provider.py`.

**Learnings:**
- The existing summary string scale can include quote precision (`500.0000`), so the regression asserts numeric value instead of string formatting.
- The portfolio test suite briefly hit container restarts/kills when run during backend startup, then passed when rerun serially.

## Notes

- Completed after the AI settings serializer lookup issue.
