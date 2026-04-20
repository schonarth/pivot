---
status: resolved
priority: p2
issue_id: "005"
tags: [code-review, ai, portfolios, cache, performance]
dependencies: []
resolved_date: 2026-04-20
---

# Stabilize scope insight cache keys across identical portfolios

## Status: ✅ RESOLVED

**Solution implemented**: Canonicalized scope assets and holdings before hashing so reordered portfolios now reuse the same AI cache entry.

## Problem Statement

The new on-demand scope insight endpoint hashes portfolio positions in whatever row order the database returns. Because position ordering is not defined, identical holdings can produce different cache keys and trigger repeated AI calls, extra spend, and inconsistent responses.

## Findings

- `get_portfolio_scope_insight()` loads positions with no `order_by()` at [backend/portfolios/services.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/portfolios/services.py#L176).
- `Position` has no model `ordering`, only a uniqueness constraint, at [backend/trading/models.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/trading/models.py#L20).
- `AIService.analyze_scope()` hashes both `holdings` and `_scope_move_signature(assets)` as-is at [backend/ai/services.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/ai/services.py#L1609), so different asset iteration order produces different `ai_scope_insight` cache keys.
- The watch flow is ordered by `-created_at`, but the portfolio-position flow is not, so cache reuse is least reliable on the portfolio side.

## Proposed Solutions

### Option 1: Sort positions and assets before building the signature

**Approach:** Add explicit ordering in `get_portfolio_scope_insight()` and normalize the `assets` / `holdings` lists before hashing.

**Pros:**
- Small targeted fix
- Makes cache behavior deterministic without changing the API

**Cons:**
- Needs careful normalization so all dependent structures stay aligned

**Effort:** 1-2 hours

**Risk:** Low

---

### Option 2: Build the scope signature from canonical tuples only

**Approach:** Derive the cache signature from sorted tuples such as `(asset_id, quantity, average_cost, move_signature)` instead of raw mutable dict/list order.

**Pros:**
- More resilient long term
- Easier to reason about cache invalidation inputs

**Cons:**
- Slightly broader refactor
- Needs updated tests for canonicalization

**Effort:** 2-3 hours

**Risk:** Medium

## Recommended Action

**To be filled during triage.**

## Technical Details

**Affected files:**
- [backend/portfolios/services.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/portfolios/services.py#L165)
- [backend/ai/services.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/ai/services.py#L1589)
- [backend/trading/models.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/trading/models.py#L11)

**Related components:**
- Portfolio scope insight endpoint
- AI budget accounting
- Cache reuse for monitored-set analysis

**Database changes (if any):**
- Migration needed: No

## Resources

- **PR:** [#30](https://github.com/schonarth/pivot/pull/30)
- **Merge commit:** `785d8433e6e9f8761270a1e6679eca3d4b1ca55e`

## Acceptance Criteria

- [ ] Repeated scope insight requests for unchanged holdings reuse the same cache entry
- [ ] Position ordering changes do not alter the scope cache key
- [ ] Regression tests cover deterministic cache reuse for portfolio positions

## Work Log

### 2026-04-19 - Review discovery

**By:** Codex

**Actions:**
- Compared the new scope insight endpoint in [backend/portfolios/views.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/portfolios/views.py#L67) with the cache key construction in [backend/ai/services.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/ai/services.py#L1609)
- Verified that `Position` has no default ordering in [backend/trading/models.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/trading/models.py#L20)
- Traced how raw `holdings` and asset-order-dependent move signatures feed the cache key

**Learnings:**
- The new on-demand design fixed summary latency, but it introduced nondeterministic cache reuse for portfolio insights
- This can directly increase AI spend because cache misses fall through to live model calls

## Notes

- This is a cache correctness issue with budget and response consistency impact.
