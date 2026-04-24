# 00 - Milestone Coordination

## Purpose

Coordinate Milestone 07 execution so the system can validate explicit paper-trade candidates against bounded technical and context evidence without turning recommendation output into hidden execution authority.

## Roadmap Milestone

Milestone 07 - Strategy Validation Layer

## Governing SPEC

SPEC-007 Strategy Validation with Technical and Context Inputs

## Status

done

## Owner

GPT-5.4 / coordination

## Date Started

2026-04-21

## Date Completed

2026-04-24

## Branch

feat/autonomous/07-strategy-validation

## Dependencies

- SPEC-007 approved
- required references:
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/roadmap.md`
  - `docs/architecture/execution/milestone-delivery-execution-model.md`
  - `docs/specs/SPEC-001-open-news-context-expansion.md`
  - `docs/specs/SPEC-002-narrative-continuity-for-asset-context.md`
  - `docs/specs/SPEC-003-context-scope-expansion-asset-portfolio-watchlist.md`
  - `docs/specs/SPEC-004-sentiment-trajectory-and-narrative-state.md`
  - `docs/specs/SPEC-005-divergence-reasoning-for-market-analysis.md`
  - `docs/specs/SPEC-006-opportunity-discovery-pipeline.md`
  - `docs/specs/SPEC-007-strategy-validation-with-technical-and-context-inputs.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/03 - portfolio-and-watch-scope/05 - portfolio-and-watch-ui-surface.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/03 - portfolio-and-watch-scope/06 - portfolio-and-watch-scope-ai-summary.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/04 - sentiment-trajectory/04 - implementation-validation-and-release-readiness.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/05 - counterfactual-and-divergence-reasoning/04 - asset-divergence-implementation-and-release-readiness.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/05 - counterfactual-and-divergence-reasoning/05 - monitored-set-extension-cli-and-validation.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/06 - opportunity-discovery/04 - discovery-implementation-and-release-readiness.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/06 - opportunity-discovery/05 - watch-handoff-refinement-and-validation.md`

## Likely Files Touched

- docs/specs/SPEC-007-strategy-validation-with-technical-and-context-inputs.md
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/07 - strategy-validation-layer/*
- backend/ai/*
- backend/mcp/*
- backend/markets/*
- backend/portfolios/*
- backend/tests/*
- frontend/src/*
- frontend/tests/*
- docs/reference/*

## Entry Conditions

- roadmap reviewed
- milestone delivery execution model reviewed
- SPEC-007 reviewed
- Milestone 03 UI surface references reviewed for monitored-set and manual-action presentation reuse
- Milestone 04 to 06 implementation references reviewed for current analysis artifact and consumer boundaries

## Task Steps

1. Read the roadmap, SPEC-007, and required prior references before implementation.
2. Confirm the current candidate-entry points for manual trade review, analysis artifact reuse, and paper-only recommendation storage.
3. Execute Milestone 07 task files in order.
4. Keep validation bounded to explicit user-supplied candidates; never infer a trade from prose or discovery output.
5. Reuse existing technical, context, trajectory, and divergence artifacts where they already exist; do not build a parallel analysis stack.
6. Keep verdicts limited to `approve`, `reject`, and `defer`.
7. Make recommendation logging canonical:
   - persist exact input snapshot
   - persist structured verdict fields
   - persist compact rationale
8. Keep user-facing prose separate from the canonical record.
9. Keep manual-trade integration explicitly opt-in:
   - conspicuous `Should I?` action near `BUY` or `SELL` button in New Trade view.
   - no automatic validation on load or input change
   - no hidden validation request on trade execution
10. Keep manual execution authority with the user regardless of verdict.
11. Treat deterministic fixture coverage and paper-review inspection as required milestone validation.
12. Make the final handoff explicit about:
   - whether recommendation logging ships end to end
   - whether the manual-trade `Should I?` surface ships end to end
   - whether any consumers beyond manual trade review were intentionally deferred
   - whether the next step should proceed directly to Milestone 08 or pause to harden operator review tooling

## Tests to Add or Update

- candidate intake validation tests
- deterministic verdict fixture tests covering approve, reject, and defer
- regression tests for recommendation record persistence
- regression tests proving manual trade execution remains non-blocking
- frontend tests for opt-in `Should I?` request behavior and advisory rendering if frontend changes land
- frontend changes are implemented

## Commands to Run

- `cd backend && ruff check .`
- `cd backend && pytest`
- `cd frontend && npm run typecheck`
- run affected frontend tests if frontend code changes
- run milestone integration tests covering candidate validation, verdict persistence, and manual-trade non-blocking behavior

## Exit Conditions

- explicit strategy candidates can be evaluated in paper mode
- every verdict stores the exact technical and context inputs used
- recommendation logging is auditable and canonical
- manual-trade integration is opt-in and non-blocking
- rejected and deferred outcomes remain first-class and reviewable
- milestone remains user-releaseable

## Implementation Notes / What Was Done

Completed Milestone 07 implementation.

What was done:

- added explicit paper candidate validation through `POST /api/ai/strategy-validation/`
- added canonical `StrategyRecommendation` storage for exact candidate and evidence snapshots
- reused existing technical indicators, context packs, sentiment trajectory, and divergence helpers
- exposed recent paper recommendations through `GET /api/ai/strategy-recommendations/`
- added an opt-in `Should I?` action near manual trade execution
- kept manual trade submission separate and non-blocking regardless of verdict
- added deterministic backend coverage for `approve`, `reject`, `defer`, persistence, and non-blocking execution
- added frontend coverage for explicit validation invocation and advisory rendering

## Open Follow-Ups

- Consumers beyond manual trade review are intentionally deferred.
- Decide before Milestone 08 whether dedicated operator review tooling should be hardened first.
