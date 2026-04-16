# 04 - Implementation, Validation, and Release Readiness

## Purpose

Integrate bounded temporal continuity into the current asset-analysis flow, validate it with representative multi-day examples, and confirm Milestone 02 is ready for a user-visible release.

## Roadmap Milestone

Milestone 02 - Temporal Narrative Continuity

## Governing ADR

ADR-002 Narrative Continuity for Asset Context

## Status

planned

## Owner

unassigned

## Branch

feat/autonomous/02-temporal-continuity

## Date Started

2026-04-16

## Date Completed

TBD

## Dependencies

- 00 - milestone coordination.md
- 01 - continuity-insertion-point-and-retained-artifact-scan.md
- 02 - retention-labeling-and-persistence-shape.md
- 03 - prompt-continuity-section-and-ingestion-sentiment.md

## Required Prior References

- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces/01 - boundary-decision-and-current-state-scan.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces/02 - shared-vocabulary-and-interface-contracts.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces/03 - current-consumers-and-storage-touchpoints.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/01 - asset-context-expansion/04 - implementation-validation-and-release-readiness.md`

## Likely Files Touched

- backend/ai/*
- backend/markets/*
- backend/tests/*
- frontend/src/*
- frontend/tests/*
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/02 - temporal-narrative-continuity/04 - implementation-validation-and-release-readiness.md

## Entry Conditions

- insertion point identified
- retention and label rules finalized
- prompt continuity section finalized
- ingestion sentiment direction finalized
- representative multi-day validation examples identified

## Background

This is the milestone integration task. Earlier task files define where continuity belongs, what retained artifact is allowed, how labels are computed, and how continuity reaches the prompt. This task applies that design to the current asset-analysis path, validates it against real multi-day examples, and confirms Milestone 02 is ready to ship.

## Detailed Requirements

- integrate continuity into the current asset-analysis flow without creating a second reasoning path
- preserve the existing asset-analysis happy path when no retained continuity signal exists
- validate at least one multi-day narrative shift for an asset
- keep Milestone 02 inside ADR-002 scope:
  - no portfolio or watch continuity
  - no sentiment trajectory states
  - no counterfactual reasoning layer
  - no strategy or autonomous behavior
- produce enough release-readiness notes that UAT can focus on continuity behavior rather than basic stability checks

## Proposed Approach

- integrate only after the insertion point, retention rules, and prompt shape are settled
- add smoke tests first for unchanged happy paths, then extend with continuity cases
- use representative examples from the real seeded asset universe and live or fixture-backed multi-day headlines
- keep frontend adaptation minimal unless the consumer surface needs a small continuity field addition
- keep ingestion-time sentiment forward-only if implemented

## Validation Scenarios

- an asset with fresh headline changes can now explain what changed across recent days
- an asset with repeated but stable story items can distinguish continuing from new
- continuity context remains absent or small when there is no meaningful prior context
- prompt noise does not materially increase
- current consumer entrypoints continue to work

## Task Steps

1. Implement the continuity layer at the selected integration point while preserving the Milestone 00 context/reasoning/execution boundary.
2. Add or update smoke coverage for the asset analysis happy path.
3. Add validation scenarios for at least one clear multi-day narrative shift and one stable continuing narrative.
4. Confirm the prompt remains compact and continuity labels remain deterministic.
5. Verify the implementation still respects Milestone 00 vocabulary, Milestone 01 context-pack boundaries, and ADR-002 storage constraints.
6. Run lint, typecheck, affected unit tests, and milestone-end integration tests.
7. Prepare UAT notes:
   - user-visible behavior change
   - known limitations
   - representative examples

## Tests to Add or Update

- smoke tests for asset analysis with continuity enabled
- unit tests for continuity labeling and prompt assembly
- regression tests preserving Milestone 01 behavior when continuity history is absent
- milestone-end integration tests covering backend/frontend handoff if frontend is affected

## Commands to Run

- `cd backend && ruff check .`
- `cd backend && pytest`
- `cd frontend && npm run typecheck`
- run affected frontend tests if frontend code changes
- run milestone integration tests covering backend/frontend handoff

## Exit Conditions

- Milestone 02 behavior implemented
- tests pass
- lint and typecheck pass
- representative multi-day validation examples exist
- user-visible release notes are ready
- task file updated with actual implementation outcome

## Implementation Notes / What Was Done

TBD

## Open Follow-Ups

- feed the representative continuity examples into Milestone 03 and Milestone 04 planning later
