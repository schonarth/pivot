# 03 - Advisory Manual Trade UI and Paper Review Surface

## Purpose

Surface strategy validation to end users in a way that is conspicuous, useful, and honest about scope: opt-in near manual trade execution, advisory only, and backed by a reviewable stored recommendation record.

## Roadmap Milestone

Milestone 07 - Strategy Validation Layer

## Governing SPEC

SPEC-007 Strategy Validation with Technical and Context Inputs

## Status

done

## Owner

Codex / implementation

## Date Started

2026-04-24

## Date Completed

2026-04-24

## Branch

feat/autonomous/07-strategy-validation

## Dependencies

- `00 - milestone coordination.md`
- `01 - candidate-intake-and-analysis-reuse-scan.md`
- `02 - deterministic-verdict-rules-and-recommendation-record-contract.md`

## Likely Files Touched

- frontend/src/views/*
- frontend/src/components/*
- frontend/tests/*
- backend/tests/*
- docs/reference/*

## Entry Conditions

- canonical verdict and recommendation record contract defined

## Background

Validation requests consume time and tokens. Milestone 07 therefore needs an explicit user action rather than a hidden trade gate. The manual trade flow should let the user ask for guidance while preserving the user's full authority to execute the trade regardless of the answer.

## Detailed Requirements

- place a conspicuous `Should I?` action near the existing `BUY` or `SELL` execute controls
- do not auto-run validation:
  - on form load
  - on input change
  - on manual trade submit
- show verdict and short rationale as advisory output only
- make the stored recommendation reviewable from a paper-review surface or equivalent inspection path
- preserve manual trade execution regardless of verdict
- keep copy and state honest about latency and optional token usage

## Proposed Approach

1. Reuse the current manual trade form rather than creating a separate hidden flow.
2. Add one explicit validation action and one result display area right next to it. Keep it minimalistic.
3. Keep trade submit separate in state, network request, and error handling.
4. Provide a lightweight review surface for stored recommendation records.

## Validation Scenarios

- user executes trade without ever requesting validation
- user requests validation, gets `reject`, then still executes trade
- user requests validation, gets `defer`, then leaves without executing
- user reviews the stored recommendation and exact evidence later

## Task Steps

1. Review the requirement and expected behavior.
2. Scan the current trade UI and adjacent inspection surfaces.
3. Implement the smallest correct opt-in validation surface.
4. Add or update regression coverage proving non-blocking manual execution.
5. Run verification commands.

## Tests to Add or Update

- frontend tests for explicit `Should I?` invocation only
- regression tests proving trade submit remains available after any verdict
- tests for advisory result rendering and review-surface access if implemented

## Commands to Run

- `cd frontend && npm run typecheck`
- run affected frontend tests

## Exit Conditions

- manual-trade validation is explicit and opt-in
- verdict display is advisory only
- manual execution remains available regardless of verdict
- stored recommendation can be inspected later

## Implementation Notes / What Was Done

- Added an explicit `Should I?` action next to manual trade execution in the new trade form.
- Kept validation out of form load, input change, and trade submit.
- Rendered verdict, compact rationale, exact evidence snapshot, and recent paper recommendations as advisory review output.
- Added frontend regression coverage proving validation is only invoked by the explicit action and trade submit remains separate.

## Open Follow-Ups

- none
