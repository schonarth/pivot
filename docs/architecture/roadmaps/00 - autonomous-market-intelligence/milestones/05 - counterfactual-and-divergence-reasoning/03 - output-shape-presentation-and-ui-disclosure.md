# 03 - Output Shape, Presentation, and UI Disclosure

## Purpose

Define the canonical structured divergence payload, the small-field presentation output layered on top of it, and the Milestone 05 UI disclosure that explains monitored-set scope limits.

## Roadmap Milestone

Milestone 05 - Counterfactual and Divergence Reasoning

## Governing ADR

ADR-005 Divergence Reasoning for Market Analysis

## Status

planned

## Owner

unassigned

## Branch

feat/autonomous/05-divergence-reasoning

## Dependencies

- 00 - milestone coordination.md
- 01 - divergence-insertion-points-and-signal-source-scan.md
- 02 - deterministic-expectation-and-classification-rules.md

## Required Prior References

- `docs/architecture/adrs/ADR-003-context-scope-expansion-asset-portfolio-watchlist.md`
- `docs/architecture/adrs/ADR-005-divergence-reasoning-for-market-analysis.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/03 - portfolio-and-watch-scope/05 - portfolio-and-watch-ui-surface.md`

## Likely Files Touched

- backend/ai/*
- backend/mcp/*
- frontend/src/*
- frontend/tests/*
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/05 - counterfactual-and-divergence-reasoning/03 - output-shape-presentation-and-ui-disclosure.md

## Entry Conditions

- deterministic outcome rules finalized
- likely UI consumers identified
- ADR-005 output and disclosure decisions reviewed

## Background

Milestone 05 needs an output contract that stays auditable for backend logic while giving the frontend enough structure to present divergence clearly. It also needs a compact disclosure so users understand that broader cross-asset reasoning only considers the current asset and explicitly monitored assets in the relevant scope.

## Detailed Requirements

- define the canonical `divergence_analysis` fields
- keep canonical divergence output structured and deterministic
- do not make prose the system of record
- define the small-field presentation shape that can sit on top of canonical fields
- avoid single-blob LLM output for divergence presentation
- define where divergence should appear in asset and scope consumers
- add a compact info-icon disclosure where divergence is shown
- keep the disclosure neutral and explanatory rather than warning-heavy
- preserve existing i18n expectations for user-facing text

## Proposed Approach

- keep the canonical backend payload minimal:
  - `label`
  - `expected_direction`
  - `actual_direction`
  - `actual_percent_move`
  - `flat_threshold_percent`
  - `signal_votes`
  - `macro_confirmation`
- let presentation text return as two or three small fields at most
- reuse existing summary-card or insight-component patterns where they fit
- add the approved scope disclosure in a popover behind an info icon near the divergence section

## Validation Scenarios

- frontend can render divergence without parsing a free-form blob
- backend can change presentation wording without changing canonical classification semantics
- UI disclosure makes the monitored-set boundary explicit
- divergence presentation remains readable for both asset and monitored-set consumers if both are in scope

## Task Steps

1. Define the canonical divergence payload fields.
2. Define the presentation-oriented text fields layered on top.
3. Identify the frontend components that should render divergence.
4. Add the milestone UI disclosure requirement and expected wording shape.
5. Identify necessary frontend and contract tests.

## Tests to Add or Update

- payload-shape tests for `divergence_analysis`
- consumer-shape tests for presentation fields if applicable
- frontend tests for disclosure rendering and info-popover behavior if frontend work lands

## Commands to Run

- `cd frontend && npm run typecheck`
- run affected frontend tests if frontend code changes
- run affected backend contract tests if payload shape changes

## Exit Conditions

- canonical output contract explicit
- presentation output contract explicit
- UI disclosure placement explicit
- frontend consumers can render divergence without free-form parsing

## Implementation Notes / What Was Done

To be filled during execution.

## Open Follow-Ups

- none
