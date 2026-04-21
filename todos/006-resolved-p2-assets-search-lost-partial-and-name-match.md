---
status: resolved
priority: p2
issue_id: "006"
tags: [code-review, frontend, assets, ux, correctness]
dependencies: []
resolved_date: 2026-04-20
---

# Restore partial and name-based asset search

## Status: ✅ RESOLVED

**Solution implemented**: Kept `searchAssets()` as the first pass for typed queries and only fell back to `lookupAssetSymbol()` when the local search returned nothing.

## Problem Statement

The Assets page no longer behaves like a search. As soon as the user types any non-empty query, the view switches from broad filtering to exact symbol lookup, so partial symbol matches and company-name matches stop working.

## Findings

- In [frontend/src/views/AssetsView.vue](/Volumes/HomeX/gus/Projects/Lab/paper-trader/frontend/src/views/AssetsView.vue#L272), `doSearch()` now routes non-empty input through `lookupAssetSymbol(...)` instead of `searchAssets(...)`.
- `lookupAssetSymbol()` in [frontend/src/api/assets.ts](/Volumes/HomeX/gus/Projects/Lab/paper-trader/frontend/src/api/assets.ts#L8) calls the exact-match `/assets/lookup-symbol/` endpoint, which only returns a symbol when the input matches a seeded or Yahoo-importable ticker exactly.
- The page copy still says "Search assets..." and "Try a different search" in [frontend/src/views/AssetsView.vue](/Volumes/HomeX/gus/Projects/Lab/paper-trader/frontend/src/views/AssetsView.vue#L18), which no longer matches the behavior.
- The previous `searchAssets()` flow on [frontend/src/api/assets.ts](/Volumes/HomeX/gus/Projects/Lab/paper-trader/frontend/src/api/assets.ts#L3) supports partial symbol and name filtering through the `/assets/` endpoint.

## Proposed Solutions

### Option 1: Keep search and lookup separate

**Approach:** Use `searchAssets()` for the text box and expose `lookupAssetSymbol()` only through an explicit "add/import symbol" action.

**Pros:**
- Restores the existing search semantics
- Keeps exact lookup behavior available where it belongs

**Cons:**
- Requires a small UI split between browse/search and import

**Effort:** 1-2 hours

**Risk:** Low

### Option 2: Fall back to broad search on no exact match

**Approach:** Try `lookupAssetSymbol()` first, but if it returns 404, fall back to `searchAssets()` so partial and name searches still work.

**Pros:**
- Preserves the new import path while restoring discoverability
- Minimal UI change

**Cons:**
- Adds branchy client behavior
- Can make the search results less predictable

**Effort:** 1 hour

**Risk:** Low

## Recommended Action


## Technical Details

**Affected files:**
- [frontend/src/views/AssetsView.vue](/Volumes/HomeX/gus/Projects/Lab/paper-trader/frontend/src/views/AssetsView.vue#L272)
- [frontend/src/api/assets.ts](/Volumes/HomeX/gus/Projects/Lab/paper-trader/frontend/src/api/assets.ts#L3)

**Related components:**
- Asset browse/search page
- Exact symbol import flow

**Database changes (if any):**
- Migration needed: No

## Resources

- **PR:** [#30](https://github.com/schonarth/pivot/pull/30)
- **Merge commit:** `785d8433e6e9f8761270a1e6679eca3d4b1ca55e`

## Acceptance Criteria

- [ ] Partial ticker queries still return matching assets
- [ ] Company-name queries still return matching assets
- [ ] Exact symbol lookup remains available for import flows
- [ ] Search page copy matches the implemented behavior

## Work Log

### 2026-04-19 - Review discovery

**By:** Codex

**Actions:**
- Compared the old `/assets/` search path with the new exact-lookup branch in [frontend/src/views/AssetsView.vue](/Volumes/HomeX/gus/Projects/Lab/paper-trader/frontend/src/views/AssetsView.vue#L272)
- Checked the API split between `searchAssets()` and `lookupAssetSymbol()` in [frontend/src/api/assets.ts](/Volumes/HomeX/gus/Projects/Lab/paper-trader/frontend/src/api/assets.ts#L3)
- Verified the current copy still presents the field as a general search box

**Learnings:**
- The new behavior is a regression from browse/search to exact-match-only lookup
- That change breaks the asset discovery workflow for partial tickers and company names

## Notes

- This is a UX regression with real functionality impact, not just wording drift.
