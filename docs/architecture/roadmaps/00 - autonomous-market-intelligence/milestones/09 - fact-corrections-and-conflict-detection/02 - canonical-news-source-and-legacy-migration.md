# 02 - Canonical News Source and Legacy Migration

## Purpose

Introduce `NewsSource` as the active source identity, migrate every existing artifact deterministically, and make new ingestion link directly to canonical sources.

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

## Likely Files Touched

- `backend/markets/models.py`
- `backend/markets/services.py`
- `backend/markets/seed_data.py`
- `backend/markets/migrations/*`
- `backend/markets/test_*.py`
- `backend/ai/news_context_policy.py`
- `backend/ai/test_context.py`

## Entry Conditions

- source mappings and ingestion insertion point documented
- migration can preserve all existing artifacts

## Detailed Requirements

- add system-managed `NewsSource` records with institution name, feed URL, and optional market
- link each news artifact to its actual `NewsSource`; legacy source text remains historical provenance only
- seed records for all current feed URLs
- map legacy `rss_feed` artifacts by linked asset market to the matching Bloomberg or Yahoo Finance source
- map other known legacy labels to canonical sources deterministically
- ensure new ingestion writes the canonical relation directly
- preserve every artifact and fail loudly on an unmapped known source rather than silently assigning a generic identity

## Validation Scenarios

- existing RSS artifact maps to the correct market-specific source
- legacy known-label artifact maps to its canonical source
- legacy provenance remains intact while active identity is relational
- new ingested artifact has a direct `NewsSource`
- market-agnostic source remains eligible across markets

## Task Steps

1. Define the minimal model, relation, migration, and seed shape from task 01 findings.
2. Implement the migration with deterministic mappings and safe data preservation.
3. Update ingestion and context reads to use the active source relation.
4. Add migration, ingestion, and eligibility tests.
5. Run migrations and focused tests in a disposable/local test environment.

## Tests to Add or Update

- `NewsSource` model and seed tests
- legacy source migration tests, including `rss_feed` market mapping
- ingestion tests proving canonical source linkage
- context-source eligibility tests

## Commands to Run

- `cd backend && python manage.py makemigrations --check`
- `cd backend && pytest markets ai/test_context.py`
- `cd backend && ruff check markets ai/news_context_policy.py`

## Exit Conditions

- active source identity is canonical and relational
- existing artifacts are preserved and deterministically mapped
- new ingestion no longer relies on generic source identity
- source-stance work can safely depend on configured sources

## Implementation Notes / What Was Done

not started

## Open Follow-Ups

- none
