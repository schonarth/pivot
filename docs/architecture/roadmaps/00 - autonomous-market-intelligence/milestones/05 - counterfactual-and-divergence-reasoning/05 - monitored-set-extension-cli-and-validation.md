# 05 - Monitored-Set Extension, CLI, and Validation

## Purpose

Extend the approved divergence contract to monitored-set consumers where shared evidence exists, unlock the narrow `competing_macro_priority` path, and finalize milestone validation with the divergence inspection CLI and documentation.

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
- 04 - asset-divergence-implementation-and-release-readiness.md

## Required Prior References

- `docs/architecture/adrs/ADR-003-context-scope-expansion-asset-portfolio-watchlist.md`
- `docs/architecture/adrs/ADR-005-divergence-reasoning-for-market-analysis.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/03 - portfolio-and-watch-scope/04 - implementation-validation-and-release-readiness.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/03 - portfolio-and-watch-scope/05 - portfolio-and-watch-ui-surface.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/04 - sentiment-trajectory/04 - implementation-validation-and-release-readiness.md`

## Likely Files Touched

- backend/ai/*
- backend/mcp/*
- backend/tests/*
- frontend/src/*
- frontend/tests/*
- docs/reference/*
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/05 - counterfactual-and-divergence-reasoning/05 - monitored-set-extension-cli-and-validation.md

## Entry Conditions

- asset-level divergence implemented
- monitored-set readiness documented
- output and UI contract already in use for asset consumers

## Background

Milestone 05 intentionally lands asset divergence first. This task reuses the same contract for monitored-set consumers where shared evidence exists, keeps `competing_macro_priority` narrow and auditable, and formalizes the CLI inspection workflow so live divergence review does not get lost in ad hoc scripts.

## Detailed Requirements

- apply the same canonical divergence contract to monitored-set consumers when implementation-ready
- avoid a separate monitored-set scoring path
- emit `competing_macro_priority` only when explicit monitored-set or shared-context evidence justifies it
- preserve honest fallback to `reversal` when broader-force confirmation is missing
- render or reuse the scope disclosure where monitored-set divergence is shown
- provide a CLI inspection tool that prints divergence inputs, structured outputs, and presentation fields together
- document the CLI tool in general project documentation once implemented
- validate the monitored-set extension against frozen fixtures and representative live/current scenarios

## Proposed Approach

- start from the working asset contract and extend it without changing core semantics
- add monitored-set-specific regression tests around shared-evidence gating
- keep CLI output human-auditable rather than minimal or machine-only
- include at least one monitored-set example that can honestly justify `competing_macro_priority`

## Validation Scenarios

- monitored-set consumers reuse the same divergence semantics as asset consumers
- `competing_macro_priority` only appears when explicit broader-force evidence exists
- same opposite-move case without monitored-set confirmation falls back to `reversal`
- CLI output shows enough inputs and outputs for human review
- CLI documentation is discoverable outside the roadmap docs

## Task Steps

1. Extend the divergence contract to monitored-set consumers.
2. Add or update regression tests around monitored-set shared-evidence behavior.
3. Implement or finalize the divergence inspection CLI.
4. Document the CLI in general project documentation.
5. Validate frozen fixtures and representative live/current scenarios.
6. Run lint, typecheck, affected tests, and milestone integration checks.
7. Prepare final handoff notes:
   - monitored-set implementation status
   - `competing_macro_priority` evidence limits
   - CLI location and documentation
   - any remaining release caveats

## Tests to Add or Update

- monitored-set divergence regression tests
- `competing_macro_priority` gating tests
- CLI smoke tests if practical
- frontend tests for monitored-set divergence rendering if frontend is in scope

## Commands to Run

- `cd backend && ruff check .`
- `cd backend && pytest`
- `cd frontend && npm run typecheck`
- run affected frontend tests if frontend code changes
- run the divergence inspection CLI against frozen fixtures and at least one live/current scenario

## Exit Conditions

- monitored-set consumers reuse the same divergence contract
- `competing_macro_priority` remains narrow and auditable
- CLI inspection tool exists and is documented in general project documentation
- representative validation examples are reviewed
- tests pass
- task file updated with actual implementation outcome

## Implementation Notes / What Was Done

To be filled during execution.

## Open Follow-Ups

- none
