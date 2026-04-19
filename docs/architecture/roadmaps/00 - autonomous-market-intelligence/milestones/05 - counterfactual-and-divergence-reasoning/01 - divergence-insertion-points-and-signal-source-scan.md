# 01 - Divergence Insertion Points and Signal Source Scan

## Purpose

Identify the smallest correct integration points and the exact reusable signals Milestone 05 should consume so divergence lands inside the shared analysis path without duplicating earlier logic.

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

## Required Prior References

- `docs/architecture/adrs/ADR-003-context-scope-expansion-asset-portfolio-watchlist.md`
- `docs/architecture/adrs/ADR-004-sentiment-trajectory-and-narrative-state.md`
- `docs/architecture/adrs/ADR-005-divergence-reasoning-for-market-analysis.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/03 - portfolio-and-watch-scope/03 - clustering-prioritization-and-composition.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/04 - sentiment-trajectory/04 - implementation-validation-and-release-readiness.md`

## Likely Files Touched

- backend/ai/*
- backend/mcp/*
- backend/markets/*
- backend/tests/*
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/05 - counterfactual-and-divergence-reasoning/01 - divergence-insertion-points-and-signal-source-scan.md

## Entry Conditions

- milestone scaffold exists
- ADR-005 reviewed
- Milestone 03 and 04 shared analysis paths reviewed

## Background

Milestone 05 reuses context, continuity, monitored-set composition, and trajectory rather than inventing a new reasoning path. This task finds the exact current integration points and source signals so later implementation tasks can stay small and architectural drift stays low.

## Detailed Requirements

- identify the current shared asset-analysis and scope-analysis entry points
- identify where technical posture, context signals, retained items, trajectory output, and recent market price data already exist
- identify the smallest insertion point for asset-level divergence
- identify whether monitored-set consumers can reuse the same divergence contract without a second scoring path
- identify where canonical structured divergence output should attach
- identify current frontend consumers likely to render divergence
- identify existing CLI or debug surfaces that can host a divergence inspection tool

## Proposed Approach

- scan the backend analysis service and surrounding composition pipeline first
- map exact reusable fields instead of proposing new broad abstractions
- check whether recent price history or equivalent move data is already available in the analysis path
- document monitored-set readiness explicitly rather than assuming parity

## Validation Scenarios

- asset analysis has one clear insertion point for divergence
- monitored-set analysis can either reuse the same contract or the exact missing gap is documented
- recent move data source is explicit enough to support thresholded net percent move
- no second parallel reasoning stack is required

## Task Steps

1. Scan the current asset-analysis and scope-analysis code paths.
2. Identify current technical, context, trajectory, and recent move inputs already available.
3. Document the smallest correct insertion point for asset divergence.
4. Document monitored-set readiness for later extension.
5. Identify likely CLI and frontend consumers for divergence output.
6. Record risks, missing data, and reuse opportunities.

## Tests to Add or Update

- none in this scan task

## Commands to Run

- `rg` searches for analysis, trajectory, scope, and recent price sources
- targeted file reads in backend and frontend

## Exit Conditions

- insertion point documented
- signal sources documented
- monitored-set readiness documented
- canonical output attachment point documented
- later tasks can implement without rediscovering core architecture

## Implementation Notes / What Was Done

To be filled during execution.

## Open Follow-Ups

- none
