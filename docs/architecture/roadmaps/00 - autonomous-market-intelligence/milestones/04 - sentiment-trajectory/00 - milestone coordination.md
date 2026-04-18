# 00 - Milestone Coordination

## Purpose

Coordinate Milestone 04 execution so the system can compute short-window sentiment trajectory for assets and explicit themes without turning trajectory into a second reasoning or execution system.

## Roadmap Milestone

Milestone 04 - Sentiment Trajectory

## Governing ADR

ADR-004 Sentiment Trajectory and Narrative State

## Status

done

## Owner

GPT-5.4 / coordination

## Date Started

2026-04-17

## Date Completed

2026-04-17

## Branch

feat/autonomous/04-sentiment-trajectory

## Dependencies

- ADR-004 approved
- required references:
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/roadmap.md`
  - `docs/architecture/execution/milestone-delivery-execution-model.md`
  - `docs/architecture/adrs/ADR-001-open-news-context-expansion.md`
  - `docs/architecture/adrs/ADR-002-narrative-continuity-for-asset-context.md`
  - `docs/architecture/adrs/ADR-003-context-scope-expansion-asset-portfolio-watchlist.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/02 - temporal-narrative-continuity/01 - continuity-insertion-point-and-retained-artifact-scan.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/02 - temporal-narrative-continuity/02 - retention-labeling-and-persistence-shape.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/02 - temporal-narrative-continuity/03 - prompt-continuity-section-and-ingestion-sentiment.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/03 - portfolio-and-watch-scope/01 - monitored-set-consumers-and-insertion-points.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/03 - portfolio-and-watch-scope/03 - clustering-prioritization-and-composition.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/03 - portfolio-and-watch-scope/04 - implementation-validation-and-release-readiness.md`

## Likely Files Touched

- docs/architecture/adrs/ADR-004-sentiment-trajectory-and-narrative-state.md
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/04 - sentiment-trajectory/*
- backend/ai/*
- backend/markets/*
- backend/mcp/*
- backend/tests/*
- frontend/src/*

## Entry Conditions

- roadmap reviewed
- milestone delivery execution model reviewed
- ADR-004 reviewed
- Milestone 02 continuity files reviewed as normative inputs
- Milestone 03 monitored-set files reviewed as normative inputs where monitored-set consumers exist

## Task Steps

1. Read the roadmap, milestone delivery execution model, ADR-004, and required prior references before implementation.
2. Confirm the current source of truth for retained selected items and per-item sentiment labels.
3. Execute Milestone 04 task files in order.
4. Implement asset-scope trajectory first.
5. Reuse the same trajectory contract for monitored-set consumers when Milestone 03 outputs are implementation-ready and doing so does not require new monitored-set surface design.
6. If monitored-set support is not implementation-ready, do not block Milestone 04; ship asset-scope trajectory cleanly first.
7. Keep trajectory deterministic before any LLM explanation.
8. Keep trajectory bounded to the same short-window continuity horizon unless an earlier task proves a narrower window is required.
9. Keep trajectory as analysis input only; do not let it cross into trade execution, approval, or autonomous action.
10. Keep theme aggregation auditable and optional; prefer asset-level trajectory whenever theme linkage is weak.
11. Prepare milestone-end validation notes that focus on user-visible trajectory explanations and price-vs-tone divergence cases.
12. Make the final milestone handoff explicit about monitored-set status:
   - whether monitored-set consumers were implementation-ready
   - whether trajectory was implemented against them
   - if not, what concrete gap prevented inclusion
   - whether the next step should proceed directly to Milestone 05 or detour to close Milestone 03/04 integration gaps

## Tests to Add or Update

- deterministic trajectory-state tests for `improving`, `deteriorating`, `conflicting`, and `reversal`
- retention-window tests proving older items do not affect the result
- regression tests for existing asset-analysis behavior when trajectory data is absent
- monitored-set regression tests if Milestone 03 consumers are part of the implementation slice

## Commands to Run

- `cd backend && ruff check .`
- `cd backend && pytest`
- `cd frontend && npm run typecheck`
- run affected frontend tests if frontend code changes
- run milestone integration tests covering trajectory output consumers

## Exit Conditions

- deterministic short-window trajectory rules are explicit
- asset-level trajectory works from the shared pipeline
- monitored-set reuse is either implemented or explicitly deferred without ambiguity
- trajectory output stays compact, auditable, and bounded
- milestone remains user-releaseable

## Implementation Notes / What Was Done

Completed Milestone 04 setup.

What was done:

- reviewed the roadmap, execution model, ADR-004, and Milestone 02 and 03 handoff files before creating the milestone scaffold
- marked ADR-004 approved so Milestone 04 artifacts can exist under the roadmap rules
- created the Milestone 04 folder and task sequence for scan, deterministic state rules, prompt and persistence shape, and release-readiness validation
- completed a refinement pass to resolve the initial open decisions around monitored-set inclusion, theme aggregation, compute-on-read trajectory, and weak-signal handling
- recorded that the current repo now appears to include real monitored-set implementation surfaces that Milestone 04 should verify and reuse when they are implementation-ready

## Open Follow-Ups

- none
