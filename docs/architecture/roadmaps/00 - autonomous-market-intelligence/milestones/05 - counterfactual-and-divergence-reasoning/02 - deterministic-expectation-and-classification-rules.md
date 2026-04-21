# 02 - Deterministic Expectation and Classification Rules

## Purpose

Define the deterministic rules that map bounded current signals and bounded recent price move into the approved Milestone 05 divergence outcomes.

## Roadmap Milestone

Milestone 05 - Counterfactual and Divergence Reasoning

## Governing SPEC

SPEC-005 Divergence Reasoning for Market Analysis

## Status

planned

## Owner

unassigned

## Branch

feat/autonomous/05-divergence-reasoning

## Dependencies

- 00 - milestone coordination.md
- 01 - divergence-insertion-points-and-signal-source-scan.md

## Required Prior References

- `docs/specs/SPEC-004-sentiment-trajectory-and-narrative-state.md`
- `docs/specs/SPEC-005-divergence-reasoning-for-market-analysis.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/04 - sentiment-trajectory/02 - deterministic-trajectory-states-and-thresholds.md`

## Likely Files Touched

- backend/ai/*
- backend/tests/*
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/05 - counterfactual-and-divergence-reasoning/02 - deterministic-expectation-and-classification-rules.md

## Entry Conditions

- insertion point documented
- available input signals documented
- SPEC-005 outcome set reviewed

## Background

Milestone 05 is only auditable if the classifier outcome is decided by explicit rules before any explanatory prose. This task defines strict-consensus expected direction, thresholded net percent move, and the full outcome matrix including `no_divergence` and `insufficient_signal`.

## Detailed Requirements

- define the expectation-stage directional vote inputs and ordering rules
- define the strict-consensus policy for `up`, `down`, `uncertainty_conflict`, and `insufficient_signal`
- define thresholded net percent move and flat classification
- define the default flat threshold constant shape and value
- define deterministic outcome mapping for:
  - `no_divergence`
  - `insufficient_signal`
  - `no_material_follow_through`
  - `reversal`
  - `competing_macro_priority`
  - `uncertainty_conflict`
- define when monitored-set/shared-context evidence is strong enough to justify `competing_macro_priority`
- define tie-breaking and no-inference rules
- keep `competing_macro_priority` rare and evidence-gated
- keep classification bounded to the short retained window
- do not rely on the LLM to decide any canonical state

## Proposed Approach

- map directional inputs into a small ordinal vote model
- apply strict consensus before checking actual move
- compute actual move from earliest and latest in-window price using percent change
- treat `uncertainty_conflict` only as expectation-stage directional disagreement
- treat weak or partial evidence as `insufficient_signal`
- treat `reversal` as the default contradiction label and require explicit broader-force confirmation for `competing_macro_priority`

## Validation Scenarios

- aligned positive expectation and positive actual move yields `no_divergence`
- aligned negative expectation and flat actual move yields `no_material_follow_through`
- opposing expectation-stage votes yield `uncertainty_conflict`
- weak or partial expectation-stage evidence yields `insufficient_signal`
- opposite actual move without broader-force confirmation yields `reversal`
- opposite actual move with explicit monitored-set/shared confirmation yields `competing_macro_priority`
- small actual move below threshold yields actual direction `flat`, which then maps to `no_material_follow_through` when a clear expectation exists or leaves the classifier at `insufficient_signal` when no clear expectation exists

## Task Steps

1. Define expectation-stage votes and strict-consensus rules.
2. Define thresholded net percent move and the flat-threshold constant.
3. Define the deterministic outcome matrix.
4. Define the monitored-set/shared-evidence threshold for `competing_macro_priority`.
5. Define edge-case and tie behavior.
6. Identify the minimum unit tests needed for each outcome and edge case.

## Tests to Add or Update

- deterministic tests for all six outcomes
- flat-threshold tests
- percent-move direction tests
- monitored-set evidence gating tests for `competing_macro_priority`

## Commands to Run

- `cd backend && ruff check .`
- run affected backend tests around divergence scoring

## Exit Conditions

- expectation-stage rules explicit
- actual-move rules explicit
- outcome matrix explicit
- ambiguous cases handled explicitly
- tests needed for implementation are identified

## Implementation Notes / What Was Done

To be filled during execution.

## Open Follow-Ups

- none
