# 03 - Correction, Review, and Treatment Contracts

## Purpose

Add audited correction, artifact-review, and per-operator source-stance records, then apply their deterministic precedence only to bounded context-selection source quality.

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

## Likely Files Touched

- `backend/ai/models.py`
- `backend/ai/services.py`
- `backend/ai/news_context_policy.py`
- `backend/ai/serializers.py`
- `backend/ai/migrations/*`
- `backend/ai/test_context.py`
- `backend/ai/test_strategy_validation.py`

## Detailed Requirements

- persist linked correction records with source artifact/type/id, `fact_key`, immutable platform-captured `original_value`, corrected value, state, reason, creator, timestamps, and supersession
- constrain correction state to `corrected`, `disputed`, or `stale`; artifact review to `accepted`, `disputed`, or `stale`; source stance to `trusted` or `untrusted`
- normalize new fact keys to lower snake case; derive operator-local suggestions only from completed corrections
- persist source stances per operator with marking, replacement, and clear-as-supersession history; never create an active neutral stance
- enforce precedence: fact correction, artifact review, source stance, baseline
- apply `+1` for accepted/trusted and `-1` for disputed/stale/untrusted solely to existing source-quality context selection, clamped to `0..4`; artifact treatment overrides source treatment
- keep disputed and stale facts categorical signals for strategy/scenario review; do not numerically alter verdict, scenario confidence, or execution decisions

## Validation Scenarios

- another operator cannot observe or affect a source stance
- clear closes the active stance and restores baseline treatment
- artifact review overrides source stance for that artifact
- quality adjustment clamps at both bounds
- `original_value` cannot be supplied or changed through the correction write path
- fact-key suggestions exclude abandoned or superseded drafts

## Task Steps

1. Define minimal record models and scoped service APIs from the scan findings.
2. Implement record lifecycle, immutable-original-value capture, normalization, and suggestion query.
3. Extend only the existing source-quality selection path with deterministic treatment.
4. Serialize structured review state needed by existing consumers.
5. Add unit and integration tests for lifecycle, precedence, scope, and bounds.

## Tests to Add or Update

- model/service tests for correction and stance lifecycle
- fact-key normalization and suggestion tests
- original-value immutability tests
- precedence and clamped source-quality tests
- per-operator source-stance isolation tests

## Commands to Run

- `cd backend && pytest ai/test_context.py ai/test_strategy_validation.py`
- `cd backend && ruff check ai`

## Exit Conditions

- correction and review records are auditable, scoped, and structured
- original evidence remains unchanged
- treatment order and bounded adjustment are deterministic and covered
- no new shared score or execution behavior exists

## Implementation Notes / What Was Done

not started

## Open Follow-Ups

- none
