# 07 - Implementation Validation and Release Readiness

## Purpose

Verify the Milestone 09 correction foundation end to end and document the exact handoff contract for future autonomous execution gating.

## Roadmap Milestone

Milestone 09 - Fact Corrections and Conflict Detection

## Governing SPEC

SPEC-009 Fact Corrections and Conflict Detection

## Status

done

## Owner

Codex / validation

## Date Started

2026-07-25

## Date Completed

2026-07-25

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

- Added controlled end-to-end evidence-treatment coverage with mock news artifacts. A disputed high-quality artifact clears the operator cache, changes selected context, moves regenerated asset and scope insights from `BUY` to `HOLD`, changes their summaries, and moves a new `BUY` strategy recommendation from `approve` to `defer`.

- Rebuilt backend validation: focused source, treatment, invalidation, review API, and MCP suite passed (`98 passed`); the full backend suite's first failure is pre-existing opportunity-discovery fixture cardinality (`ai/test_discovery.py::TestOpportunityDiscovery::test_discovery_endpoint_returns_structured_shortlist`, expected 1, received 2).
- Migration check has no Milestone 09 delta. It only proposes existing `markets` and `portfolios` index renames. A validation-found constraint representation mismatch that proposed an AI migration was corrected without changing its database contract.
- Fixed a Milestone 09 UI source-stance regression: `NewsSource` uses an integer primary key, while the UI serializer and clear route expected UUIDs, causing valid source-stance mutations to return 400/404. The UI now uses the canonical integer identity and its focused endpoint test passes.
- Frontend typecheck and the focused Evidence review component suite pass. The full Vitest suite has existing failures in `DiscoveryView` status rendering and an incomplete `AssetsView` module mock. Playwright passes 19/20; the existing registration smoke test expects a JSON refresh token that the authentication API does not return.
- MCP schema and API reference document scoped evidence retrieval and bounded correction, artifact-review, and source-stance operations. Milestone 10 may consume only the structured, read-only correction/artifact-review history, current treatment, categorical uncertainty, and permanent invalidation state; it must not infer trade execution authority from these records.

## Open Follow-Ups

- Full-suite baseline failures listed above are unrelated to Milestone 09 and remain outside this task's scope.
