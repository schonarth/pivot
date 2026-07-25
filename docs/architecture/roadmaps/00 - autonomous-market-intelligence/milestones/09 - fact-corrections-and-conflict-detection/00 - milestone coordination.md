# 00 - Milestone Coordination

## Purpose

Coordinate Milestone 09 so operators can record factual corrections and evidence conflicts without rewriting historical evidence or enabling autonomous execution.

## Roadmap Milestone

Milestone 09 - Fact Corrections and Conflict Detection

## Governing SPEC

SPEC-009 Fact Corrections and Conflict Detection

## Status

done

## Owner

Codex / coordination

## Date Started

2026-07-25

## Date Completed

2026-07-25

## Branch

feat/autonomous/09-fact-corrections

## Dependencies

- SPEC-009 approved
- required references:
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/roadmap.md`
  - `docs/architecture/execution/milestone-delivery-execution-model.md`
  - `docs/specs/SPEC-007-strategy-validation-with-technical-and-context-inputs.md`
  - `docs/specs/SPEC-008-scenario-framing-for-strategy-decisions.md`
  - `docs/specs/SPEC-009-fact-corrections-and-conflict-detection.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/07 - strategy-validation-layer/00 - milestone coordination.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/07 - strategy-validation-layer/02 - deterministic-verdict-rules-and-recommendation-record-contract.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/07 - strategy-validation-layer/03 - advisory-manual-trade-ui-and-paper-review-surface.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/08 - scenario-and-risk-framing/01 - recommendation-evidence-and-risk-source-scan.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/08 - scenario-and-risk-framing/02 - scenario-frame-contract-and-validation.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/08 - scenario-and-risk-framing/03 - generation-persistence-and-risk-framing.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/08 - scenario-and-risk-framing/04 - advisory-and-review-scenario-surfaces.md`

## Likely Files Touched

- `backend/markets/*`
- `backend/ai/*`
- `backend/mcp/*`
- `backend/*/migrations/*`
- `frontend/src/api/*`
- `frontend/src/types/*`
- `frontend/src/views/*`
- `frontend/src/components/*`
- `frontend/src/**/__tests__/*`
- `docs/reference/*`

## Entry Conditions

- roadmap and milestone delivery execution model read in full
- SPEC-009 read and adopted as the source of truth
- Milestone 07 and the named Milestone 08 task files read and adopted as working constraints
- no SPEC-009 decision remains open
- Milestone 08's unresolved scenario-quality work is understood as separate from this correction foundation; do not expand this milestone to repair it

## Task Steps

1. Read all required references before implementation.
2. Execute tasks 01 through 07 in order.
3. Preserve source artifacts and recommendation snapshots; corrections are linked audit records, never rewrites.
4. Treat fact corrections, artifact review states, and source stances as structured, scoped records with deterministic precedence.
5. Make `NewsSource` the active source identity before source-stance behavior is used.
6. Apply only the specified bounded `source_quality` adjustment to context selection; do not add a shared score or alter verdicts, confidence bands, or execution decisions numerically.
7. Make material corrections and disputed or stale artifact states create permanent reverse recommendation invalidations; source stances affect future selection only.
8. Keep UI and MCP operations on the same scoped backend behavior, with immutable platform-captured `original_value` and assistant audit identity.
9. Keep all review controls advisory and operator initiated. Do not create AI conflict queues or autonomous execution.
10. Complete end-to-end, unit, and integration verification before handoff.

## Tests to Add or Update

- source identity and legacy migration coverage
- correction, artifact review, and source-stance lifecycle/precedence coverage
- bounded context-selection adjustment and invalidation coverage
- scoped UI and MCP operation coverage
- end-to-end coverage for disabled and override-enabled source stances plus fact-key suggestions and normalization

## Commands to Run

- `cd backend && ruff check .`
- `cd backend && pytest`
- `cd frontend && npm run typecheck`
- run affected frontend unit tests
- run affected end-to-end tests
- run milestone integration tests for source migration, correction persistence, invalidation, UI, and MCP parity

## Exit Conditions

- every artifact has an active canonical `NewsSource` identity before source stances are enabled
- corrections and review states preserve original evidence and audit history
- deterministic treatment and invalidation rules are covered and applied consistently
- strategy-recommendation and scenario-review surfaces expose evidence review and correction state
- MCP provides equivalent authenticated, audited operations
- no autonomous execution or AI-generated conflict queue is introduced
- milestone remains a mergeable foundation for Milestone 10

## Implementation Notes / What Was Done

- Tasks 01 through 07 completed. Canonical source migration, correction/review treatment, permanent recommendation invalidation, advisory Evidence review UI, and scoped MCP parity are implemented and verified by the rebuilt backend focused suite (98 passing tests) and focused frontend suite/typecheck.
- Task 07 fixed the validated integer `NewsSource` UI source-stance contract mismatch and documented the MCP evidence contract. Future autonomous gating receives read-only structured treatment, correction/review history, categorical uncertainty, and invalidation state only; no execution behavior was added.

## Open Follow-Ups

- Existing baseline failures remain outside Milestone 09: opportunity-discovery fixture cardinality in the full backend suite; DiscoveryView rendering and AssetsView mock errors in the full frontend unit suite; registration smoke test expects a JSON refresh token absent from the authentication response (Playwright 19/20).
