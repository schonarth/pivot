---
status: resolved
priority: p2
issue_id: "004"
tags: [code-review, markets, scheduling, data-integrity, api]
dependencies: []
resolved_date: 2026-04-20
---

# Make asset lookup import resilient to backfill queue failures

## Status: ✅ RESOLVED

**Solution implemented**: Wrapped the OHLCV backfill enqueue in `backend/markets/services.py` so lookup still returns the imported asset when the queue is temporarily unavailable.

## Problem Statement

The new symbol lookup flow creates an `Asset` row before enqueueing OHLCV backfill, but it does not handle broker failures around `.delay()`. A queue outage can leave a partially imported asset in the database, return `500`, and prevent future lookups from retrying the missing backfill.

## Findings

- [backend/markets/services.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/markets/services.py#L191) persists the asset via `get_or_create_asset(...)`.
- The very next step calls `backfill_single_asset_ohlcv.delay(...)` at [backend/markets/services.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/markets/services.py#L205) with no exception handling.
- If the Celery broker is unavailable, the request fails after the asset row already exists.
- Subsequent lookups short-circuit on the local exact match at [backend/markets/services.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/markets/services.py#L155) and never retry the missed backfill, so the imported symbol can remain without OHLCV history indefinitely.
- Both [backend/markets/views.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/markets/views.py#L44) and [backend/mcp/views.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/mcp/views.py#L211) inherit this failure mode.

## Proposed Solutions

### Option 1: Catch enqueue failures and still return the asset

**Approach:** Wrap `.delay()` in `try/except`, log the failure, return the asset, and allow a later repair/backfill path to fill history.

**Pros:**
- Prevents partial-import `500`s
- Keeps lookup usable during queue incidents

**Cons:**
- Asset may still be returned before history is available

**Effort:** 1 hour

**Risk:** Low

---

### Option 2: Mark backfill-needed state and retry on later lookups

**Approach:** Persist a field or derived condition indicating missing OHLCV backfill, and enqueue again when a later exact-match lookup finds an incomplete asset.

**Pros:**
- Self-heals after transient queue failures
- Avoids permanently stranded imported assets

**Cons:**
- Requires schema or extra branching
- Slightly larger design change

**Effort:** 2-4 hours

**Risk:** Medium

## Recommended Action

**To be filled during triage.**

## Technical Details

**Affected files:**
- [backend/markets/services.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/markets/services.py#L150)
- [backend/markets/views.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/markets/views.py#L44)
- [backend/mcp/views.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/mcp/views.py#L211)
- [backend/markets/tasks.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/markets/tasks.py#L68)

**Related components:**
- Yahoo symbol lookup
- Celery broker / OHLCV backfill queue

**Database changes (if any):**
- Migration needed: No for Option 1
- Migration needed: Maybe for Option 2

## Resources

- **PR:** [#30](https://github.com/schonarth/pivot/pull/30)
- **Merge commit:** `785d8433e6e9f8761270a1e6679eca3d4b1ca55e`

## Acceptance Criteria

- [ ] Lookup endpoints do not fail just because the backfill queue is temporarily unavailable
- [ ] Imported assets with missing OHLCV history can be retried automatically or manually
- [ ] Regression tests cover broker/enqueue failure behavior

## Work Log

### 2026-04-19 - Review discovery

**By:** Codex

**Actions:**
- Traced the symbol lookup flow from [backend/markets/views.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/markets/views.py#L44) into [backend/markets/services.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/markets/services.py#L150)
- Confirmed asset persistence happens before asynchronous backfill enqueue
- Checked the local exact-match fast path that suppresses future remote lookup attempts

**Learnings:**
- The new import path can leave behind partially initialized assets
- A transient infrastructure failure can become a persistent data gap

## Notes

- This is both an operational resilience problem and a data completeness problem.
