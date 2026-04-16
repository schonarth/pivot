# 04 - Implementation, Validation, and Release Readiness

## Purpose

Integrate scope-aware monitored-set intelligence into the current pipeline, validate it for asset, portfolio, and watch consumers, and confirm Milestone 03 is ready for a user-visible release.

## Roadmap Milestone

Milestone 03 - Portfolio and Watch Scope

## Governing ADR

ADR-003 Context Scope Expansion: Asset, Portfolio, Watchlist

## Status

planned

## Owner

unassigned

## Branch

feat/autonomous/03-scope-expansion

## Dependencies

- 00 - milestone coordination.md
- 01 - monitored-set-consumers-and-insertion-points.md
- 02 - scope-contracts-and-watch-membership.md
- 03 - clustering-prioritization-and-composition.md

## Required Prior References

- `docs/architecture/adrs/ADR-001-open-news-context-expansion.md`
- `docs/architecture/adrs/ADR-002-narrative-continuity-for-asset-context.md`
- `docs/architecture/adrs/ADR-003-context-scope-expansion-asset-portfolio-watchlist.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces/02 - shared-vocabulary-and-interface-contracts.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces/03 - current-consumers-and-storage-touchpoints.md`

## Likely Files Touched

- backend/ai/*
- backend/markets/*
- backend/portfolios/*
- backend/mcp/*
- backend/tests/*
- frontend/src/*
- frontend/tests/*
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/03 - portfolio-and-watch-scope/04 - implementation-validation-and-release-readiness.md

## Entry Conditions

- insertion point documented
- scope contract finalized
- clustering and prioritization rules finalized
- required prior references reviewed

## Background

This is the milestone integration task. The earlier task files define where the change belongs, how monitored sets resolve membership, and how shared events should be clustered and prioritized. This task applies that design to the current analysis path and validates the result against real monitored-set use cases.

## Detailed Requirements

- integrate scope-aware context composition into the shared pipeline
- preserve the current asset-intelligence happy path while adding `portfolio` and `watch`
- validate the first concrete authenticated UI portfolio intelligence consumer
- validate the first concrete authenticated UI watch intelligence consumer
- keep the milestone inside ADR-003 scope:
  - no inferred discovery
  - no autonomous trading
  - no cross-asset narrative engine beyond monitored-set composition
  - no separate bespoke reasoning stack for each scope
- prepare enough release-readiness notes that UAT can focus on monitored-set usefulness rather than basic correctness

## Proposed Approach

- integrate only after the insertion point, scope contract, and clustering rules are settled
- add regression coverage for unchanged asset behavior first
- add monitored-set tests for explicit membership, clustering, and prioritization
- validate with at least one portfolio example and one watch example using actual seeded assets or realistic fixtures
- keep frontend adaptation minimal by reusing the shared producer path and asset-scope drill-down contract rather than embedding full asset detail inline

## Validation Scenarios

- existing asset analysis still works with `scope_type=asset`
- a portfolio summary surfaces clustered shared events plus unique asset items
- a watch summary works without open positions
- the same asset can participate in both portfolio and watch scopes without identity confusion
- ambiguous overlap stays separate rather than over-clustered, including cases like one `0.80` match paired only with weak `0.25` and `0.20` matches
- monitored-set output keeps affected assets visible and fetchable through stable IDs

## Task Steps

1. Implement scope-aware context composition at the selected integration point.
2. Add or update explicit watch membership support if required by the chosen contract.
3. Add regression coverage for the existing asset path.
4. Add monitored-set tests for scope resolution, clustering, prioritization, and consumer output shape.
5. Validate at least one portfolio consumer and one watch consumer end to end.
6. Run lint, typecheck, affected unit tests, and milestone integration checks.
7. Prepare UAT notes:
   - user-visible behavior change
   - known limitations
   - representative portfolio and watch examples

## Tests to Add or Update

- regression tests for `asset` scope
- unit tests for watch membership and scope resolution
- clustering and prioritization tests for monitored-set output
- backend/frontend handoff tests for the first portfolio and watch consumers

## Commands to Run

- `cd backend && ruff check .`
- `cd backend && pytest`
- `cd frontend && npm run typecheck`
- run affected frontend tests if frontend code changes
- run milestone integration tests covering monitored-set consumers

## Exit Conditions

- `asset`, `portfolio`, and `watch` scopes work from one shared pipeline
- watch membership is explicit and durable enough for the first consumer
- duplicate shared stories are clustered when appropriate
- asset-level traceability is preserved
- tests pass
- release-readiness notes are ready
- task file updated with actual implementation outcome

## Implementation Notes / What Was Done

Not started.

## Open Follow-Ups

- confirm whether Milestone 04 sentiment trajectory should consume monitored-set outputs directly or through the same asset-first retained items
