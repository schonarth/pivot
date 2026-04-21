# 06 - Portfolio and Watch Scope AI Summary

## Purpose

Add a single AI summary for the portfolio scope and a single AI summary for the watch scope, while keeping asset-level analysis available as drill-down underneath.

## Roadmap Milestone

Milestone 03 - Portfolio and Watch Scope

## Governing SPEC

SPEC-003 Context Scope Expansion: Asset, Portfolio, Watchlist

## Status

done

## Owner

GPT-5 / coding

## Branch

feat/autonomous/03-scope-expansion

## Date Started

2026-04-16

## Date Completed

2026-04-16

## Dependencies

- 00 - milestone coordination.md
- 01 - monitored-set-consumers-and-insertion-points.md
- 02 - scope-contracts-and-watch-membership.md
- 03 - clustering-prioritization-and-composition.md
- 04 - implementation-validation-and-release-readiness.md
- 05 - portfolio and watch UI surface.md

## Required Prior References

- `docs/specs/SPEC-001-open-news-context-expansion.md`
- `docs/specs/SPEC-002-narrative-continuity-for-asset-context.md`
- `docs/specs/SPEC-003-context-scope-expansion-asset-portfolio-watchlist.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces/02 - shared-vocabulary-and-interface-contracts.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces/03 - current-consumers-and-storage-touchpoints.md`

## Likely Files Touched

- backend/ai/*
- backend/portfolios/*
- backend/mcp/*
- backend/tests/*
- frontend/src/api/*
- frontend/src/components/*
- frontend/src/views/PortfolioDetailView.vue
- frontend/src/views/AssetDetailView.vue
- frontend/src/router/index.ts
- frontend/src/types/index.ts
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/03 - portfolio-and-watch-scope/06 - portfolio-and-watch-scope-ai-summary.md

## Entry Conditions

- milestone 03 scope contract and watch membership are already defined
- monitored-set composition rules are already defined
- the portfolio/watches UI surface exists
- the current asset AI surface remains intact
- SPEC-004 remains untouched

## Background

The current portfolio UI improved the browsing experience, but it still only exposes asset-by-asset AI analysis inside the portfolio view. Milestone 03 needs a true monitored-set result: one portfolio-level AI insight for the whole portfolio and one watch-level AI insight for the whole watch scope. The asset-level analysis should stay visible, but only as drill-down below the scope summary.

## Detailed Requirements

- add one portfolio-level AI insight that summarizes the whole portfolio scope
- add one watch-level AI insight that summarizes the whole watch scope
- keep the asset-level analysis in the portfolio view as secondary drill-down
- keep the asset-level analysis on the asset page unchanged
- keep the portfolio and watch summaries on the same shared monitored-set pipeline
- reuse the existing asset analysis path only where needed for drill-down or continuity reuse
- do not add a separate reasoning stack for portfolio or watch
- do not touch SPEC-004

## Proposed Approach

- add a scope-aware AI endpoint or service entry point that accepts `scope_type`, `scope_id`, and `as_of`
- have the portfolio page render one primary AI summary card for the portfolio scope
- have the watches tab render one primary AI summary card for the watch scope
- keep the asset-by-asset analysis component below the summary card as optional drill-down
- preserve the asset detail route as the deepest drill-down surface
- if the current portfolio/watch binding is sufficient, reuse it instead of inventing a second watch model

## Validation Scenarios

- a portfolio page shows one portfolio-level AI summary before any asset cards
- a watches tab shows one watch-level AI summary before any asset cards
- the asset-level analysis remains visible underneath the scope summary
- the portfolio summary changes when holdings change
- the watch summary changes when watch membership changes
- the asset detail page still shows the standalone asset AI analysis
- the same asset can still appear in both scope summary and drill-down without confusion

## Task Steps

1. Define the scope-level AI result shape for portfolio and watch.
2. Decide the smallest backend entry point for scope-aware analysis.
3. Add the portfolio-level and watch-level summary cards to the portfolio UI.
4. Keep asset-level analysis visible below the summary card.
5. Preserve the asset detail analysis route and existing asset AI behavior.
6. Add regression coverage for the new scope-level summary.
7. Run backend and frontend verification.

## Tests to Add or Update

- scope-aware AI service tests
- portfolio summary rendering tests
- watch summary rendering tests
- regression tests preserving asset-level drill-down
- frontend typecheck and affected component tests

## Commands to Run

- `cd backend && ruff check .`
- `cd backend && pytest`
- `cd frontend && npm run typecheck`
- run affected frontend tests if frontend code changes

## Exit Conditions

- portfolio scope shows one AI summary for the whole portfolio
- watch scope shows one AI summary for the whole watch set
- asset-level analysis remains available underneath as drill-down
- asset detail analysis remains unchanged
- tests pass
- task file updated with actual implementation outcome

## Implementation Notes / What Was Done

- Added scope-aware AI insight generation in [`backend/ai/services.py`](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/ai/services.py) with shared monitored-set prompt assembly and caching.
- Extended [`backend/portfolios/services.py`](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/portfolios/services.py) so portfolio summaries now include `scope_insights` for both portfolio positions and watch assets.
- Reflected the new summary contract in [`backend/portfolios/serializers.py`](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/portfolios/serializers.py) and covered it in [`backend/portfolios/test_views.py`](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/portfolios/test_views.py).
- Added the reusable scope summary UI in [`frontend/src/components/ScopeInsightCard.vue`](/Volumes/HomeX/gus/Projects/Lab/paper-trader/frontend/src/components/ScopeInsightCard.vue) and rendered it in [`frontend/src/views/PortfolioDetailView.vue`](/Volumes/HomeX/gus/Projects/Lab/paper-trader/frontend/src/views/PortfolioDetailView.vue) above the existing position and watch drill-down sections.
- Extended [`frontend/src/types/index.ts`](/Volumes/HomeX/gus/Projects/Lab/paper-trader/frontend/src/types/index.ts) with the monitored-scope insight contract and added [`frontend/src/components/__tests__/ScopeInsightCard.spec.ts`](/Volumes/HomeX/gus/Projects/Lab/paper-trader/frontend/src/components/__tests__/ScopeInsightCard.spec.ts).
- Verified with `docker compose exec backend pytest portfolios/test_views.py -q -k scope_insights`, `docker compose exec backend pytest ai/test_context.py -q -k scope`, `docker compose exec backend ruff check ...`, `cd frontend && npm run typecheck`, and the focused frontend component tests.

## Open Follow-Ups

- confirm whether the scope-level summary should use the same prompt format for portfolio and watch with only the asset set changing
- confirm whether the portfolio tab should show the summary above positions and the watches tab should show the summary above watch assets
