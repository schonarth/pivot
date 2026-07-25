# 04 - Recommendation Invalidation and Evidence API

## Purpose

Make correction state available to recommendation and scenario review, and permanently invalidate affected stored recommendations without mutating their snapshots.

## Roadmap Milestone

Milestone 09 - Fact Corrections and Conflict Detection

## Governing SPEC

SPEC-009 Fact Corrections and Conflict Detection

## Status

 done

## Owner

Codex / implementation

## Date Started

2026-07-25

## Date Completed

2026-07-25

## Branch

feat/autonomous/09-fact-corrections

## Dependencies

- `00 - milestone coordination.md`
- `02 - canonical-news-source-and-legacy-migration.md`
- `03 - correction-review-and-treatment-contracts.md`

## Likely Files Touched

- `backend/ai/models.py`
- `backend/ai/strategy_validation.py`
- `backend/ai/serializers.py`
- `backend/ai/views.py`
- `backend/ai/urls.py`
- `backend/ai/migrations/*`
- `backend/ai/test_strategy_validation.py`
- `backend/ai/test_views.py`

## Detailed Requirements

- add reverse `RecommendationInvalidation` records linked to the recommendation and triggering correction or artifact-state record
- create invalidations for material fact corrections and artifact `disputed`/`stale` states when stored context includes the affected artifact in the same operator scope
- do not invalidate on source-stance changes
- determine `is_invalidated` at query time from related invalidations and preload the newest triggering record for explanation
- keep recommendations immutable and invalidation permanent; revisiting creates a fresh recommendation through the existing validation path
- expose cited artifact excerpt, current treatment, correction history, categorical uncertainty, and invalidation state through the existing review API contract

## Validation Scenarios

- material correction invalidates each matching recommendation in the same operator scope
- a different operator's recommendation is unchanged
- source stance affects only future context selection
- an invalidated recommendation retains its original snapshot and never reactivates
- query response reports current invalidation state and explanation without writing data

## Task Steps

1. Define the minimal reverse-record schema and context-artifact matching strategy.
2. Implement idempotent invalidation creation in the shared correction/artifact-state service.
3. Extend recommendation queries and serializers with read-only evidence and invalidation state.
4. Confirm scenario-review consumers receive the same evidence contract through their recommendation relation.
5. Add persistence, scope, query, and no-retroactive-source-stance tests.

## Tests to Add or Update

- invalidation creation and idempotency tests
- cross-operator isolation tests
- immutable recommendation snapshot tests
- serializer/query tests for `is_invalidated` and latest explanation
- source-stance non-invalidation regression test

## Commands to Run

- `cd backend && pytest ai/test_strategy_validation.py ai/test_views.py`
- `cd backend && ruff check ai`

## Exit Conditions

- affected recommendations become permanently and audibly invalidated
- review responses expose evidence treatment and invalidation state
- historical recommendation snapshots remain untouched
- source stances never retroactively invalidate recommendations

## Implementation Notes / What Was Done

- Added permanent reverse invalidation records with exactly one linked fact correction or artifact review trigger, plus idempotent matching against stored `news_item_id` context in the operator's recommendations.
- Material fact corrections and disputed or stale artifact reviews now invalidate matching snapshots; accepted reviews and source stances do not. Existing recommendation verdict, confidence, execution behavior, and stored context remain unchanged.
- Extended strategy recommendation responses with stored excerpt evidence, current treatment, correction and artifact-review history, categorical disputed/stale uncertainty, `is_invalidated`, and latest trigger explanation. Scenario frames remain nested under that same recommendation contract.
- Added focused invalidation, scope, immutable snapshot, source-stance exclusion, and response-contract coverage. Task 04 coverage passed in the rebuilt container; the task-targeted run reached 36 passing tests.

## Open Follow-Ups

- The shared target suite has one unrelated Task 05 source-count failure (`expected 1`, `got 5` after canonical source seeding). Focused Ruff has two unrelated Task 05 long lines in `ai/views.py` (lines 233 and 314). Task 04 changed-file lint is otherwise clean.
