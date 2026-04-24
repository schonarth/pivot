# 04 - Validation Implementation and Release Readiness

## Purpose

Implement the Milestone 07 slice end to end and close release-readiness with deterministic tests, non-blocking manual-trade verification, and explicit notes about what remains deferred to later milestones.

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
- `03 - advisory-manual-trade-ui-and-paper-review-surface.md`

## Likely Files Touched

- backend/ai/*
- backend/mcp/*
- backend/portfolios/*
- backend/tests/*
- frontend/src/*
- frontend/tests/*
- docs/reference/*

## Entry Conditions

- prior Milestone 07 task files completed or explicitly narrowed

## Background

Milestone 07 should ship as a coherent user-facing recommendation layer, not as a loose backend primitive. This task is responsible for the final implementation slice, milestone-wide verification, and explicit handoff notes for Milestone 08 and beyond.

## Detailed Requirements

- implement explicit candidate validation end to end
- persist recommendation records canonically
- keep manual trade execution non-blocking
- ensure verdict fixtures remain deterministic and reviewable
- document any intentionally deferred consumer or operator tooling

## Validation Scenarios

- approve flow from explicit request through stored record
- reject flow with preserved manual trade execution
- defer flow with reviewable stored evidence
- regression check that manual trade submit never depends on validation response

## Task Steps

1. Review the requirement and expected behavior.
2. Implement the smallest complete Milestone 07 slice.
3. Add or update regression coverage.
4. Run lint, typecheck, and affected tests.
5. Document actual outcome, gaps, and next-step recommendation.

## Tests to Add or Update

- backend verdict and persistence tests
- backend or integration tests proving execution boundary stays closed
- frontend tests for opt-in advisory flow if frontend changes land
- milestone integration tests covering request, storage, and non-blocking execute behavior

## Commands to Run

- `cd backend && ruff check .`
- `cd backend && pytest`
- `cd frontend && npm run typecheck`
- run affected frontend tests

## Exit Conditions

- milestone behavior works end to end
- deterministic fixtures pass
- manual-trade execution remains non-blocking
- release notes and follow-ups are explicit
- milestone remains user-releaseable

## Implementation Notes / What Was Done

- Shipped explicit paper candidate validation end to end through `POST /api/ai/strategy-validation/`.
- Persisted canonical recommendation records and exposed recent records through `GET /api/ai/strategy-recommendations/`.
- Kept manual trade execution non-blocking, including after a rejected validation verdict.
- Added backend verdict and persistence tests plus frontend opt-in advisory-flow tests.
- Verified full backend tests, changed-file backend lint, frontend typecheck, and affected frontend tests.

## Open Follow-Ups

- Consumers beyond manual trade review are intentionally deferred.
- Dedicated operator review tooling can be hardened before Milestone 08 if broader audit workflows are needed.
