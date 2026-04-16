# 05 - Portfolio and Watch UI Surface

## Purpose

Add the first authenticated UI surface for monitored-set intelligence so a portfolio can show its positions and its watch-bound assessments in one place.

## Roadmap Milestone

Milestone 03 - Portfolio and Watch Scope

## Governing ADR

ADR-003 Context Scope Expansion: Asset, Portfolio, Watchlist

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

## Required Prior References

- `docs/architecture/adrs/ADR-001-open-news-context-expansion.md`
- `docs/architecture/adrs/ADR-002-narrative-continuity-for-asset-context.md`
- `docs/architecture/adrs/ADR-003-context-scope-expansion-asset-portfolio-watchlist.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces/02 - shared-vocabulary-and-interface-contracts.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces/03 - current-consumers-and-storage-touchpoints.md`

## Likely Files Touched

- backend/ai/*
- backend/portfolios/*
- backend/mcp/*
- frontend/src/api/*
- frontend/src/components/*
- frontend/src/views/PortfolioDetailView.vue
- frontend/src/router/index.ts
- backend/tests/*
- frontend/tests/*
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/03 - portfolio-and-watch-scope/05 - portfolio-and-watch-ui-surface.md

## Entry Conditions

- milestone coordination complete
- monitored-set consumers and insertion point documented
- scope contract and watch membership documented
- clustering and prioritization rules documented
- current authenticated UI surfaces traced
- ADR-004 remains untouched

## Background

The milestone currently has the backend and documentation shape for monitored-set intelligence, but no first-class authenticated UI surface for portfolio or watch assessments. The UI needs to make the existing portfolio page the home for monitored-set analysis instead of introducing a separate standalone watch app.

## Detailed Requirements

- add a portfolio-bound intelligence surface to the authenticated portfolio UI
- surface portfolio positions and watch-bound assessments in the same authenticated view
- keep watch surfaced as part of the portfolio experience on the frontend
- allow the watch binding to be explicit in the schema if needed for durability and clarity
- reuse the same assessment UI components for portfolio and watch
- only vary the scope-specific asset set and any required position metadata
- keep the current asset detail AI surface intact
- preserve asset drill-down from monitored-set assessments back to the existing asset detail path
- do not touch ADR-004

## Proposed Approach

- add one shared monitored-set assessment component that can render either portfolio or watch scope
- place the watch surface inside the authenticated portfolio detail page, preferably as a tab next to positions
- let the portfolio tab remain the home for positions and summary data
- keep the watch tab or section visually consistent with the portfolio assessment surface so the user sees one coherent experience
- if the backend requires a watch entity to be attached to a portfolio for this UI, prefer the smallest explicit association that keeps membership auditable
- reuse existing authenticated patterns rather than building a new standalone route unless routing is required by the data model

## Validation Scenarios

- a portfolio page shows positions and a watch-bound assessment surface in the same authenticated view
- the watch surface reuses the same assessment UI component shape as the portfolio surface
- the same asset can appear in portfolio positions and in the watch scope without confusion
- asset drill-down from the monitored-set surface still opens the existing asset detail analysis path
- empty watch state is handled cleanly without breaking portfolio positions or summary rendering
- the current asset analysis tab remains unchanged

## Task Steps

1. Decide the smallest backend shape needed to attach watch scope to a portfolio for the frontend.
2. Add the shared frontend assessment component for portfolio and watch scope.
3. Wire the portfolio detail page to show positions plus watch-bound assessments.
4. Keep the current asset detail AI surface intact.
5. Add or update tests for the new UI surface and any new backend contract.
6. Run frontend typecheck and affected tests.

## Tests to Add or Update

- portfolio detail UI rendering tests
- shared assessment component tests
- backend contract tests for portfolio/watch scope retrieval if needed
- frontend typecheck coverage for the new props and data shape

## Commands to Run

- `cd frontend && npm run typecheck`
- run affected frontend tests if frontend code changes
- run affected backend tests if schema or endpoints change

## Exit Conditions

- portfolio detail view shows positions and watch-bound assessments in the same authenticated UI
- shared assessment component is reused for both scope types
- asset drill-down still lands on the existing asset detail path
- no ADR-004 changes were made
- task file updated with actual implementation outcome

## Implementation Notes / What Was Done

- Added `PortfolioWatchMembership` in [`backend/portfolios/models.py`](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/portfolios/models.py) and a matching migration in [`backend/portfolios/migrations/0005_portfoliowatchmembership.py`](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/portfolios/migrations/0005_portfoliowatchmembership.py).
- Extended [`backend/portfolios/services.py`](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/portfolios/services.py) so `/api/portfolios/{id}/summary/` returns `watch_assets` alongside positions and publishes portfolio updates when watch membership changes.
- Added portfolio watch add/remove handling in [`backend/portfolios/views.py`](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/portfolios/views.py) with matching frontend calls in [`frontend/src/api/portfolios.ts`](/Volumes/HomeX/gus/Projects/Lab/paper-trader/frontend/src/api/portfolios.ts).
- Updated [`backend/portfolios/serializers.py`](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/portfolios/serializers.py) to reflect the summary contract.
- Added a watch membership regression test in [`backend/portfolios/test_views.py`](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/portfolios/test_views.py).
- Added [`frontend/src/components/MonitoredSetAssessment.vue`](/Volumes/HomeX/gus/Projects/Lab/paper-trader/frontend/src/components/MonitoredSetAssessment.vue) as the shared monitored-set assessment surface with optional remove controls.
- Wired the authenticated portfolio page in [`frontend/src/views/PortfolioDetailView.vue`](/Volumes/HomeX/gus/Projects/Lab/paper-trader/frontend/src/views/PortfolioDetailView.vue) to show positions plus a nested Watches tab and inline watch add/remove controls using the shared assessment component.
- Wired [`frontend/src/views/AssetDetailView.vue`](/Volumes/HomeX/gus/Projects/Lab/paper-trader/frontend/src/views/AssetDetailView.vue) to add an asset to watch and then navigate to the target portfolio's Watches tab.
- Extended [`frontend/src/types/index.ts`](/Volumes/HomeX/gus/Projects/Lab/paper-trader/frontend/src/types/index.ts) with the monitored-set summary contract.
- Added [`frontend/src/components/__tests__/MonitoredSetAssessment.spec.ts`](/Volumes/HomeX/gus/Projects/Lab/paper-trader/frontend/src/components/__tests__/MonitoredSetAssessment.spec.ts).
- Verified backend lint on the touched portfolio files, frontend typecheck, the monitored-set component test, and the portfolio regression test.

## Open Follow-Ups

None.
