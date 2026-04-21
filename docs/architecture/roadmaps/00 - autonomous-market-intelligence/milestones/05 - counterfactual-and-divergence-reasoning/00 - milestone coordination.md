# 00 - Milestone Coordination

## Purpose

Coordinate Milestone 05 execution so the system can compute deterministic short-window divergence for asset analysis first, then extend the same contract to monitored-set consumers without inventing a second reasoning or execution system.

## Roadmap Milestone

Milestone 05 - Counterfactual and Divergence Reasoning

## Governing SPEC

SPEC-005 Divergence Reasoning for Market Analysis

## Status

done

## Owner

GPT-5.4 / coordination

## Date Started

2026-04-18

## Date Completed

2026-04-18

## Branch

feat/autonomous/05-divergence-reasoning

## Dependencies

- SPEC-005 approved
- required references:
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/roadmap.md`
  - `docs/architecture/execution/milestone-delivery-execution-model.md`
  - `docs/specs/SPEC-001-open-news-context-expansion.md`
  - `docs/specs/SPEC-002-narrative-continuity-for-asset-context.md`
  - `docs/specs/SPEC-003-context-scope-expansion-asset-portfolio-watchlist.md`
  - `docs/specs/SPEC-004-sentiment-trajectory-and-narrative-state.md`
  - `docs/specs/SPEC-005-divergence-reasoning-for-market-analysis.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/03 - portfolio-and-watch-scope/03 - clustering-prioritization-and-composition.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/03 - portfolio-and-watch-scope/04 - implementation-validation-and-release-readiness.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/03 - portfolio-and-watch-scope/05 - portfolio-and-watch-ui-surface.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/04 - sentiment-trajectory/02 - deterministic-trajectory-states-and-thresholds.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/04 - sentiment-trajectory/04 - implementation-validation-and-release-readiness.md`

## Likely Files Touched

- docs/specs/SPEC-005-divergence-reasoning-for-market-analysis.md
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/05 - counterfactual-and-divergence-reasoning/*
- backend/ai/*
- backend/markets/*
- backend/mcp/*
- backend/tests/*
- frontend/src/*
- frontend/tests/*
- docs/reference/*

## Entry Conditions

- roadmap reviewed
- milestone delivery execution model reviewed
- SPEC-005 reviewed
- Milestone 03 monitored-set files reviewed as normative inputs for shared-context reuse
- Milestone 04 trajectory files reviewed as normative inputs for signal reuse

## Task Steps

1. Read the roadmap, milestone delivery execution model, SPEC-005, and required prior references before implementation.
2. Confirm the current shared analysis insertion points for asset analysis and monitored-set analysis.
3. Execute Milestone 05 task files in order.
4. Implement asset-level divergence first as the smallest complete milestone slice.
5. Keep expected-direction and label classification deterministic before any LLM explanation.
6. Keep actual move bounded to the same short window and use thresholded net percent move.
7. Keep divergence as analysis input only; do not let it cross into trade execution, approval, or autonomous action.
8. Emit `competing_macro_priority` only when explicit monitored-set or shared-context evidence exists; otherwise fall back to the other honest labels.
9. Keep user-facing prose separate from the canonical structured divergence record.
10. Add the UI disclosure where divergence is rendered so scope limits remain honest to users.
11. Treat the CLI inspection tool as part of milestone validation and document it in general project documentation once it exists.
12. Make the final milestone handoff explicit about monitored-set status:
   - whether monitored-set extension was implemented
   - whether `competing_macro_priority` was wired against explicit shared evidence
   - if not, what concrete gap blocked that extension
   - whether the next step should proceed directly to Milestone 06 or detour to close Milestone 05 integration gaps

## Tests to Add or Update

- deterministic divergence classification tests for all milestone outcomes
- flat-threshold and percent-move regression tests
- regression tests for existing asset-analysis behavior when divergence data is absent
- monitored-set regression tests if the monitored-set extension is implemented in the slice
- frontend tests for divergence presentation and scope disclosure if frontend changes land

## Commands to Run

- `cd backend && ruff check .`
- `cd backend && pytest`
- `cd frontend && npm run typecheck`
- run affected frontend tests if frontend code changes
- run milestone integration tests covering divergence consumers

## Exit Conditions

- deterministic divergence rules are explicit
- asset-level divergence works from the shared pipeline
- monitored-set reuse is either implemented or explicitly deferred without ambiguity
- divergence output stays compact, auditable, and bounded
- UI disclosure is present where divergence is shown
- milestone remains user-releaseable

## Implementation Notes / What Was Done

Completed Milestone 05 setup.

What was done:

- reviewed the roadmap, execution model, SPEC-005, and Milestone 03 and 04 handoff files before creating the milestone scaffold
- created the Milestone 05 folder and task sequence for insertion-point scan, deterministic classification rules, output and UI contract, asset-first implementation, monitored-set extension, and validation readiness
- aligned the scaffold with the approved Milestone 05 decisions:
  - strict-consensus expected direction
  - thresholded net percent move with a tunable `0.5%` flat threshold
  - explicit classifier outcomes including `no_divergence` and `insufficient_signal`
  - rare monitored-set-gated `competing_macro_priority`
  - asset-first rollout followed by monitored-set extension
  - structured canonical output with small-field presentation text on top

## Open Follow-Ups

- none
