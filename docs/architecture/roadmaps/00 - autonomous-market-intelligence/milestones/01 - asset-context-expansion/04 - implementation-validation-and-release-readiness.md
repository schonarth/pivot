# 04 - Implementation, Validation, and Release Readiness

## Purpose

Integrate the broader asset context pack into the current analysis flow, validate it against representative assets, and confirm Milestone 01 is ready for a user-visible release.

## Roadmap Milestone

Milestone 01 - Asset Context Expansion

## Governing ADR

ADR-001 Open News Context Expansion

## Status

planned

## Owner

unassigned

## Branch

feat/autonomous/01-asset-context

## Date Started

not started

## Date Completed

not started

## Dependencies

- 00 - milestone coordination.md
- 01 - existing-pipeline-scan-and-insertion-point.md
- 02 - source-selection-tagging-and-config-shape.md
- 03 - deduplication-ranking-and-context-pack-shape.md

## Likely Files Touched

- backend/*
- frontend/*
- backend/tests/*
- frontend/src/*
- frontend/tests/*
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/01 - asset-context-expansion/04 - implementation-validation-and-release-readiness.md

## Entry Conditions

- source bucket rules finalized
- context pack shape finalized
- insertion point identified

## Background

This is the milestone integration task. The earlier task files define where the change belongs and what the new context-builder behavior should be. This task applies that design to the current asset-analysis flow, validates it against representative assets, and confirms the milestone is ready to ship as a user-visible improvement.

## Detailed Requirements

- integrate the broader context-building step into the current asset-analysis path
- preserve the existing asset-analysis happy path while improving relevant cases
- validate at least three representative assets from different supported markets
- include examples where the main driver does not mention the asset symbol directly
- keep the milestone inside ADR-001 scope:
  - no narrative continuity
  - no sentiment trajectory
  - no counterfactual reasoning layer
  - no portfolio aggregation
  - no strategy or autonomous behavior
- produce enough release-readiness notes that UAT can focus on user-visible behavior rather than basic stability checks

## Proposed Approach

- integrate only after the insertion point, source rules, and context-pack shape are settled
- add smoke tests first for the unchanged happy path, then extend with broader-context cases
- select representative validation assets from the actual seeded universe after scanning what exists in the repo
- if frontend code is affected, prefer minimal adaptation to the new payload or analysis output shape
- prepare concise examples that can later seed Milestone 02 narrative validation

## Validation Scenarios

- a symbol-specific headline path still works
- an asset influenced mainly by sector or macro context now receives useful supporting headlines even when the symbol is absent
- at least one representative validation case comes from a non-BR market
- prompt budget is respected after integration
- backend/frontend handoff continues to work if the consumer surface changes

## Task Steps

1. Implement the context-building step at the selected integration point.
2. Add or update smoke coverage for the asset analysis happy path.
3. Add validation scenarios for at least three representative assets from different supported markets, selected after scanning the seeded asset universe.
4. Confirm broader context improves analysis when relevant drivers do not mention the symbol directly.
5. Run lint, typecheck, affected unit tests, and milestone-end integration tests.
6. Prepare UAT notes:
   - user-visible behavior change
   - known limitations
   - representative examples

## Tests to Add or Update

- smoke tests for asset analysis with broader context
- unit tests for representative source bucket and ranking behavior
- regression tests preserving existing symbol-only happy paths where still applicable
- milestone-end integration tests covering backend and frontend handoff if frontend is affected

## Commands to Run

- `cd backend && ruff check .`
- `cd backend && pytest`
- `cd frontend && npm run typecheck`
- run affected frontend tests if frontend code changes
- run milestone integration tests covering backend/frontend handoff

## Exit Conditions

- Milestone 01 behavior is implemented
- tests pass
- lint and typecheck pass
- representative multi-market validation examples exist
- user-visible release notes are ready
- task file updated with actual implementation outcome

## Implementation Notes / What Was Done

Not started.

## Open Follow-Ups

- feed the representative examples into Milestone 02 narrative validation later
