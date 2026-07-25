# 01 - Evidence and Source Insertion Point Scan

## Purpose

Identify the smallest safe insertion points for canonical source identity, correction records, deterministic treatment, recommendation invalidation, UI review, and MCP parity.

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

## Likely Files Touched

- `backend/markets/models.py`
- `backend/markets/services.py`
- `backend/ai/models.py`
- `backend/ai/services.py`
- `backend/ai/strategy_validation.py`
- `backend/ai/views.py`
- `backend/mcp/*`
- `frontend/src/views/TradeNewView.vue`
- `frontend/src/api/ai.ts`
- `frontend/src/types/index.ts`

## Entry Conditions

- milestone coordination and required prior references read
- current `NewsItem`, context-selection, recommendation, scenario, frontend review, and MCP paths available for inspection

## Background

The milestone must extend existing evidence flows, not create a parallel fact-checking workspace or recommendation stack. Existing source text (`rss_feed` included), context selection, recommendation snapshots, and review consumers must be mapped before persistence contracts are added.

## Detailed Requirements

- map current source fields, ingestion paths, and all known source labels/feed URLs
- map recommendation context snapshot structure and the reverse lookup needed to find recommendations containing an artifact
- map source-quality calculation and its safe extension point
- map recommendation and scenario review API/UI consumers
- map MCP authentication, operator scope, and assistant identity propagation
- identify a platform-controlled source-artifact excerpt/value extraction path for immutable `original_value`
- record concrete gaps or blockers; do not invent contracts during the scan

## Task Steps

1. Scan the named backend and frontend paths plus their tests.
2. Trace one news artifact from ingestion through bounded context selection and stored recommendation evidence.
3. Trace one recommendation through API, strategy review, and scenario review surfaces.
4. Trace one authenticated MCP request through scope enforcement and audit identity.
5. Document the chosen insertion points in this task's implementation notes before dependent implementation begins.
6. Add tests only if correcting a discovered scan defect requires code changes.
7. Run focused verification for any changed code.

## Tests to Add or Update

- none expected unless scan findings require a corrective code change

## Commands to Run

- `cd backend && pytest ai/test_context.py ai/test_strategy_validation.py markets/test_services.py mcp/test_views.py`
- `cd frontend && npm run typecheck`

## Exit Conditions

- canonical insertion points and data ownership are explicit
- known legacy source mappings are enumerated
- immutable-original-value extraction source is identified
- invalidation lookup and UI/MCP parity paths are identified
- any blocker is concrete and escalated

## Implementation Notes / What Was Done

not started

## Open Follow-Ups

- none
