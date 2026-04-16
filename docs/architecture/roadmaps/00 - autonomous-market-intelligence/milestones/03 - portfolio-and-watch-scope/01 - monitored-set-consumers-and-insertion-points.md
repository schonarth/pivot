# 01 - Monitored-Set Consumers and Insertion Points

## Purpose

Identify the smallest correct insertion points for adding portfolio and watch scope support without creating a second analysis pipeline.

## Roadmap Milestone

Milestone 03 - Portfolio and Watch Scope

## Governing ADR

ADR-003 Context Scope Expansion: Asset, Portfolio, Watchlist

## Status

done

## Owner

GPT-5.4 / coordination

## Date Started

2026-04-16

## Date Completed

2026-04-16

## Branch

feat/autonomous/03-scope-expansion

## Dependencies

- 00 - milestone coordination.md

## Required Prior References

- `docs/architecture/adrs/ADR-001-open-news-context-expansion.md`
- `docs/architecture/adrs/ADR-002-narrative-continuity-for-asset-context.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces/03 - current-consumers-and-storage-touchpoints.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/01 - asset-context-expansion/01 - existing-pipeline-scan-and-insertion-point.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/01 - asset-context-expansion/04 - implementation-validation-and-release-readiness.md`

## Likely Files Touched

- backend/ai/*
- backend/markets/*
- backend/portfolios/*
- backend/mcp/*
- frontend/src/*
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/03 - portfolio-and-watch-scope/01 - monitored-set-consumers-and-insertion-points.md

## Entry Conditions

- milestone coordination reviewed
- ADR-003 reviewed
- required prior references reviewed

## Background

Milestone 03 should extend the current asset-intelligence path rather than fork a separate portfolio or watch reasoning stack. This task exists to force a fresh scan of the real consumers and insertion points before any schema or prompt work starts.

## Detailed Requirements

- identify the current asset-intelligence producer path that Milestone 03 must extend
- identify the authenticated UI portfolio intelligence surface as the first concrete portfolio consumer
- identify the authenticated UI watch intelligence surface as the first concrete watch consumer
- identify whether any watchlist or explicit monitored-asset concept already exists in models, APIs, or UI
- find the smallest insertion point where scope-aware context composition can be added without:
  - moving execution logic into context building
  - duplicating prompt assembly in parallel services
  - bypassing asset-level continuity reuse
- call out coupling risks that would make monitored-set composition unsafe

## Proposed Approach

- start from existing frontend and MCP consumers and trace back to the shared backend producer path
- treat the authenticated UI as the first user-visible consumer for both `portfolio` and `watch`; keep MCP compatibility in view, but do not let MCP-first design widen the milestone
- confirm whether scope-aware composition should happen before prompt assembly or inside a narrow context-builder adapter
- document missing watch-scope primitives separately from implementation details
- prefer reusing the current asset-analysis service boundary unless the scan proves it cannot carry scope-aware inputs cleanly

## Validation Scenarios

- after this scan, an implementation agent should know where `scope_type`, `scope_id`, and `as_of` enter the pipeline
- the file should confirm the first concrete portfolio consumer and first concrete watch consumer in the authenticated UI path
- if current code already contains watchlist-adjacent data structures, they should be named explicitly
- if the current asset-analysis path is too coupled, the file should recommend the smallest new abstraction needed

## Task Steps

1. Review the required prior references before rescanning code.
2. Trace the current asset-intelligence flow from user-facing and agent-facing entrypoints into the shared analysis producer.
3. Identify current or near-term monitored-set consumers for portfolio and watch scope.
4. Identify whether explicit watch membership already exists anywhere in backend or frontend code.
5. Record the minimal safe insertion point for scope-aware context composition.
6. Call out coupling risks that would blur context building, reasoning, persistence, or execution.

## Tests to Add or Update

- add or update smoke coverage around the chosen insertion point once implementation begins
- preserve current asset consumer behavior while adding new scope-aware consumers

## Commands to Run

- `cd backend && ruff check .`
- run affected backend tests around AI, portfolios, and MCP consumers
- `cd frontend && npm run typecheck` if frontend files are touched

## Exit Conditions

- first monitored-set consumers are identified
- minimal insertion point is documented
- watch-scope gaps are explicit
- later implementation tasks can proceed without rediscovering the consumer graph

## Implementation Notes / What Was Done

Completed the consumer and insertion-point scan.

What was found:

- the shared backend producer path is still `AIService.analyze_asset` in `backend/ai/services.py`
- the authenticated UI asset intelligence surface is `frontend/src/components/AssetAnalysisTab.vue`, which calls `frontend/src/api/assets.ts` and the `/api/assets/{id}/ai-insight/` endpoint
- the MCP agent-facing equivalent is `backend/mcp/views.py` via `/api/mcp/asset-insight/`
- there is no current authenticated UI portfolio intelligence surface to extend; the nearest authenticated portfolio view is `frontend/src/views/PortfolioDetailView.vue`, but it only handles summary, positions, alerts, and strategies
- there is no current authenticated UI watch intelligence surface and no explicit watchlist or monitored-set model/API/UI in the codebase
- the narrowest safe insertion point remains the shared asset-analysis path, ideally just before prompt assembly in `AIService.analyze_asset` or inside a very small adapter around `build_asset_context_pack`

Coupling risks:

- `build_asset_context_pack` still mixes selection, dedupe, and shape construction directly against `NewsItem`
- prompt assembly is still adjacent to the context builder, so a new monitored-set layer should stay narrow and avoid creating a parallel reasoning path
- any portfolio or watch support must preserve asset-level continuity reuse and should not move execution logic into context composition

## Open Follow-Ups

- confirm whether the first implementation milestone should add a dedicated monitored-set adapter or extend `AIService.analyze_asset` directly
