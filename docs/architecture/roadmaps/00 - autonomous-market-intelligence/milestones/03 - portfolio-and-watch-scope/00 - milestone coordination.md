# 00 - Milestone Coordination

## Purpose

Coordinate Milestone 03 execution so the system can build intelligence for one asset, one portfolio, and one watch scope from the same underlying pipeline without duplicating stories or mixing analysis with execution.

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

- ADR-003 approved
- required references:
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/roadmap.md`
  - `docs/architecture/execution/milestone-delivery-execution-model.md`
  - `docs/architecture/adrs/ADR-001-open-news-context-expansion.md`
  - `docs/architecture/adrs/ADR-002-narrative-continuity-for-asset-context.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces/02 - shared-vocabulary-and-interface-contracts.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces/03 - current-consumers-and-storage-touchpoints.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/01 - asset-context-expansion/01 - existing-pipeline-scan-and-insertion-point.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/01 - asset-context-expansion/03 - deduplication-ranking-and-context-pack-shape.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/01 - asset-context-expansion/04 - implementation-validation-and-release-readiness.md`

## Likely Files Touched

- docs/architecture/adrs/ADR-003-context-scope-expansion-asset-portfolio-watchlist.md
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/03 - portfolio-and-watch-scope/*
- backend/ai/*
- backend/markets/*
- backend/portfolios/*
- backend/mcp/*
- frontend/src/*

## Entry Conditions

- roadmap reviewed
- milestone delivery execution model reviewed
- ADR-003 reviewed
- required prior references reviewed and treated as normative inputs
- milestone folder exists only because ADR-003 is approved
- first concrete consumers fixed for this milestone:
  - portfolio: authenticated UI portfolio intelligence surface
  - watch: authenticated UI watch intelligence surface backed by the same shared producer path

## Task Steps

1. Read the roadmap, milestone delivery execution model, ADR-003, and required prior references in full before implementation.
2. Scan the current codebase for the existing asset-level context and analysis flow, portfolio summary consumers, and any watchlist-adjacent models or APIs.
3. Execute the milestone task files in order.
4. Keep one shared context vocabulary across `asset`, `portfolio`, and `watch`.
5. Keep monitored-set membership explicit and deterministic.
6. Reuse asset-level context selection and continuity artifacts before composing monitored-set views.
7. Keep clustering, prioritization, reasoning, and execution concerns separate.
8. Prepare milestone-end validation notes that focus on user-visible monitored-set intelligence behavior.

## Tests to Add or Update

- monitored-set context-pack coverage for `asset`, `portfolio`, and `watch`
- regression coverage for existing asset-level consumers
- clustering and prioritization tests for shared macro or sector stories
- end-to-end validation for at least one portfolio summary and one watch summary consumer

## Commands to Run

- `cd backend && ruff check .`
- `cd backend && pytest`
- `cd frontend && npm run typecheck`
- run affected frontend tests if frontend code changes
- run milestone integration tests covering monitored-set intelligence consumers

## Exit Conditions

- one shared pipeline supports `asset`, `portfolio`, and `watch` scopes
- watch scope exists as an explicit monitored set without open positions
- duplicate stories across monitored assets are clustered when overlap is obvious
- asset-level traceability remains visible inside monitored-set summaries
- milestone remains user-releaseable

## Implementation Notes / What Was Done

Not started.

## Open Follow-Ups

- confirm exact route and component names for the first authenticated UI portfolio and watch consumers
