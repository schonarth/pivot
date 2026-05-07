---
name: Discovery Query Inputs Bulk Loaded
description: Opportunity discovery repeated technical, quote, and news queries per candidate asset
type: performance-issues
issue_id: "011"
tags: [opportunity-discovery, django-orm, query-observability, n-plus-one, performance]
severity: medium
status: resolved
---

# Discovery Query Inputs Bulk Loaded

## Problem

`GET /api/ai/discovery/` scaled database queries with the number of eligible candidate assets. During normal app exploration, the query observability endpoint showed discovery as the heaviest retained path.

Live query fingerprints showed repeated reads for:
- OHLCV history
- latest technical indicators
- latest asset quotes
- recent news context

This made discovery sensitive to market universe size even though the endpoint is intended to be a bounded deterministic shortlist.

### Root Cause

`backend/ai/discovery.py` scored each asset in a loop. Inside that loop, `_technical_bundle()` fetched:
- `OHLCV` rows for the current asset
- latest `TechnicalIndicators` for the current asset
- latest `AssetQuote` for the current asset
- context items through `AIService.build_asset_context_pack()`, which loaded recent `NewsItem` rows

That produced classic per-asset query repetition.

## Solution Implemented

Bulk-load discovery inputs once per discovery run, then pass the already-loaded data into per-asset scoring.

### Key Changes

**File**: `backend/ai/discovery.py`

1. Load all eligible asset IDs once after market and held-position filtering.
2. Bulk-load OHLCV rows for all eligible assets and group them by `asset_id`.
3. Bulk-load latest technical indicators ordered by `asset_id`, `-date`.
4. Bulk-load latest quotes ordered by `asset_id`, `-fetched_at`.
5. Load recent news items once and reuse them while classifying context for each asset.
6. Keep `_technical_bundle()` backward-compatible for callers that do not pass preloaded data.

**File**: `backend/ai/services.py`

`AIService.build_asset_context_pack()` accepts optional preloaded `news_items`; if omitted, it preserves the original query behavior.

## Verification

Regression test added:

`backend/ai/test_discovery.py::TestOpportunityDiscovery::test_discovery_bulk_loads_technical_inputs`

The test builds multiple discovery candidates, runs `OpportunityDiscoveryService.discover("US")`, captures Django queries, and asserts:
- one OHLCV query
- one technical indicators query
- one asset quotes query
- one news items query

Checks run:
- `docker compose exec backend pytest ai/test_discovery.py -q`
- `docker compose exec backend pytest -q`
- targeted `ruff check` for touched discovery files

Live validation after the fix showed `GET /api/ai/discovery/?market=US` at 9 queries, with each major discovery input loaded once.

## Acceptance Criteria Met

- Discovery no longer repeats technical-input queries per eligible asset
- Discovery no longer repeats recent-news queries per surviving asset
- Discovery output shape and ranking semantics remain unchanged
- Regression test fails on the old per-asset query pattern

## Impact

- **Scope**: `GET /api/ai/discovery/`
- **Behavior**: Response payload and ranking intent unchanged; data access pattern changed
- **Performance**: Query count reduced and made less sensitive to eligible asset count
- **Persistence**: No migrations or schema changes
- **Security**: No auth, permission, or secret-handling changes

## Related

- Query observability ADR: [`ADR-008-global-in-memory-query-observability.md`](../adrs/ADR-008-global-in-memory-query-observability.md)
- Discovery design ADR: [`ADR-006-two-stage-bounded-discovery.md`](../adrs/ADR-006-two-stage-bounded-discovery.md)
- Discovery spec: [`SPEC-006-opportunity-discovery-pipeline.md`](../specs/SPEC-006-opportunity-discovery-pipeline.md)
