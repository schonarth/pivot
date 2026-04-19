# 04 - Asset Divergence Implementation and Release Readiness

## Purpose

Implement deterministic asset-level divergence end to end, validate the user-visible output, and confirm the first complete Milestone 05 slice is ready for release.

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
- 03 - output-shape-presentation-and-ui-disclosure.md

## Required Prior References

- `docs/architecture/adrs/ADR-004-sentiment-trajectory-and-narrative-state.md`
- `docs/architecture/adrs/ADR-005-divergence-reasoning-for-market-analysis.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/04 - sentiment-trajectory/04 - implementation-validation-and-release-readiness.md`

## Likely Files Touched

- backend/ai/*
- backend/markets/*
- backend/mcp/*
- backend/tests/*
- frontend/src/*
- frontend/tests/*
- docs/reference/*
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/05 - counterfactual-and-divergence-reasoning/04 - asset-divergence-implementation-and-release-readiness.md

## Entry Conditions

- insertion point documented
- deterministic rules finalized
- output and UI contract finalized
- required prior references reviewed

## Background

This is the first complete Milestone 05 implementation slice. It applies deterministic divergence to asset analysis, exposes the structured and presentation outputs, adds the UI disclosure where divergence is shown, and validates that the milestone improves explanations without changing execution behavior.

## Detailed Requirements

- integrate deterministic divergence into the shared asset-analysis path
- preserve current asset-analysis behavior when divergence inputs are absent
- compute actual move on read from bounded recent price data
- implement all approved milestone outcomes:
  - `no_divergence`
  - `insufficient_signal`
  - `no_material_follow_through`
  - `reversal`
  - `uncertainty_conflict`
  - `competing_macro_priority` only if asset-scope shared evidence truly exists
- keep canonical divergence output structured and deterministic
- keep user-facing prose in small display fields rather than one large blob
- render divergence and the scope disclosure in the relevant asset UI surface
- add or update a CLI inspection tool for divergence if that fits this slice cleanly
- keep the milestone inside ADR-005 scope:
  - no trade approval logic
  - no autonomous triggers
  - no long-horizon divergence history
- if the CLI tool lands here, document it in general project documentation

## Proposed Approach

- add regression coverage for unchanged asset behavior first
- integrate deterministic divergence computation at the chosen asset insertion point
- expose the compact `divergence_analysis` section to downstream reasoning and consumers
- validate representative user-visible examples with frozen fixtures
- add the UI disclosure at the same time the divergence section is surfaced
- include the CLI tool in this task if it does not overcouple the asset slice; otherwise leave it for Task 05 with explicit handoff

## Validation Scenarios

- current asset analysis still works when no usable divergence evidence is present
- aligned expectation and actual move produce `no_divergence`
- weak or partial expectation evidence produces `insufficient_signal`
- conflicting expectation-stage votes produce `uncertainty_conflict`
- flat bounded-window move after a clear expectation produces `no_material_follow_through`
- opposite bounded-window move without broader-force confirmation produces `reversal`
- divergence UI includes the scope disclosure

## Task Steps

1. Implement deterministic asset-level divergence at the selected integration point.
2. Add or update regression coverage for the existing asset path.
3. Add unit tests for the approved outcomes and edge cases.
4. Expose the structured divergence section and small-field presentation output to asset consumers.
5. Render the UI disclosure where divergence is shown.
6. Run lint, typecheck, affected unit tests, and milestone integration checks.
7. Prepare UAT notes:
   - user-visible behavior change
   - representative examples
   - known limitations
8. In the final handoff, state explicitly:
   - whether the CLI tool landed in this slice
   - whether `competing_macro_priority` is realistically available at asset scope yet
   - whether monitored-set extension should proceed immediately next

## Tests to Add or Update

- regression tests for existing asset analysis
- deterministic divergence outcome tests
- percent-move and flat-threshold tests
- payload-shape tests for `divergence_analysis`
- frontend tests for asset divergence rendering and disclosure if frontend is in scope

## Commands to Run

- `cd backend && ruff check .`
- `cd backend && pytest`
- `cd frontend && npm run typecheck`
- run affected frontend tests if frontend code changes
- run milestone integration tests covering asset divergence consumers

## Exit Conditions

- asset-level divergence is implemented deterministically
- canonical output stays bounded and auditable
- UI disclosure is present in the asset surface
- execution behavior is unchanged
- tests pass
- release-readiness notes are ready
- task file updated with actual implementation outcome

## Implementation Notes / What Was Done

To be filled during execution.

## Open Follow-Ups

- none
