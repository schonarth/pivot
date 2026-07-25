# 07 - Implementation Validation and Release Readiness

## Purpose

Verify the Milestone 09 correction foundation end to end and document the exact handoff contract for future autonomous execution gating.

## Roadmap Milestone

Milestone 09 - Fact Corrections and Conflict Detection

## Governing SPEC

SPEC-009 Fact Corrections and Conflict Detection

## Status

planned

## Owner

unassigned

## Date Started

not started

## Date Completed

not started

## Branch

feat/autonomous/09-fact-corrections

## Dependencies

- `00 - milestone coordination.md`
- `01 - evidence-and-source-insertion-point-scan.md`
- `02 - canonical-news-source-and-legacy-migration.md`
- `03 - correction-review-and-treatment-contracts.md`
- `04 - recommendation-invalidation-and-evidence-api.md`
- `05 - evidence-review-ui-and-source-stance-controls.md`
- `06 - mcp-evidence-review-and-correction-parity.md`

## Likely Files Touched

- `backend/ai/*`
- `backend/markets/*`
- `backend/mcp/*`
- `frontend/src/*`
- `frontend/e2e/*`
- `docs/reference/*`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/09 - fact-corrections-and-conflict-detection/*`

## Entry Conditions

- tasks 01 through 06 complete or explicitly narrowed
- data migration has been exercised against representative legacy data
- focused backend, frontend, and MCP tests are runnable

## Detailed Requirements

- verify migration, correction lifecycle, deterministic precedence, bounded quality treatment, invalidation, review UI, and MCP parity together
- verify source-stances are disabled by default at zero/one eligible configured source and enabled under the development/test override
- verify no correction, review, or source stance changes historical evidence or recommendation snapshots
- verify source stances do not invalidate recommendations
- document the read-only correction/invalidation inputs available to Milestone 10; do not implement execution
- list any existing test-suite baseline failures separately from milestone failures

## Validation Scenarios

- migrated artifact reaches recommendation evidence with a canonical source
- correction captured from artifact preserves verbatim original value and invalidates matching recommendation
- disputed artifact presents categorical uncertainty in recommendation and scenario review
- clear source stance leaves audit history and restores baseline future selection
- second operator and unauthorized MCP assistant cannot access the first operator's records
- UI and MCP equivalent action yield the same treatment and invalidation state
- no operation places, blocks, or numerically scores a trade

## Task Steps

1. Review implementation notes from tasks 01 through 06.
2. Run migrations and all focused backend, frontend, MCP, and end-to-end verification.
3. Execute the validation scenarios with representative fixtures.
4. Fix only Milestone 09 regressions found by verification.
5. Update task and coordination statuses, owners, dates, actual outcome, limitations, and future gating handoff.

## Tests to Add or Update

- milestone integration test covering migration through invalidation and review rendering
- end-to-end source-control disabled/override-enabled coverage
- end-to-end fact-key suggestion and normalization coverage
- MCP/UI parity integration coverage

## Commands to Run

- `cd backend && ruff check .`
- `cd backend && pytest`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run test`
- `cd frontend && npx playwright test`
- run focused MCP and cross-service integration tests

## Exit Conditions

- all Milestone 09 behavior is demonstrably auditable and scoped
- migration and deterministic rules are verified end to end
- source-control and fact-key acceptance coverage passes
- no known milestone-scoped blocker remains
- handoff to future autonomous gating is explicit and read-only

## Implementation Notes / What Was Done

not started

## Open Follow-Ups

- none
