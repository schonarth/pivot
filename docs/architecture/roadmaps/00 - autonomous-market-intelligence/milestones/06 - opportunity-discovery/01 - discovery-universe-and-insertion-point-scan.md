# 01 - Discovery Universe and Insertion Point Scan

## Purpose

Identify the exact market-scoped asset universe, technical-data prerequisites, existing discovery consumer surfaces, and watch insertion points so Milestone 06 lands on current architecture instead of inventing a parallel path.

## Roadmap Milestone

Milestone 06 - Opportunity Discovery

## Governing ADR

ADR-006 Opportunity Discovery Pipeline

## Status

planned

## Owner

unassigned

## Branch

feat/autonomous/06-opportunity-discovery

## Dependencies

- 00 - milestone coordination.md

## Required Prior References

- `docs/architecture/adrs/ADR-003-context-scope-expansion-asset-portfolio-watchlist.md`
- `docs/architecture/adrs/ADR-006-opportunity-discovery-pipeline.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/03 - portfolio-and-watch-scope/04 - implementation-validation-and-release-readiness.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/03 - portfolio-and-watch-scope/05 - portfolio-and-watch-ui-surface.md`

## Likely Files Touched

- backend/markets/*
- backend/mcp/*
- backend/tests/*
- frontend/src/*
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/06 - opportunity-discovery/01 - discovery-universe-and-insertion-point-scan.md

## Entry Conditions

- coordination file reviewed
- ADR-006 reviewed
- required prior references reviewed

## Background

Milestone 06 assumes the current stored asset set in one explicit market is the eligible universe. Before implementing any filters or ranking, we need the exact insertion points for asset selection, quote or technical data access, surfaced discovery consumers, and explicit watch insertion behavior.

## Detailed Requirements

- identify the current source of truth for "all assets in a market"
- identify what technical data already exists and what data must be computed or fetched for discovery
- identify existing surfaces that can display a discovery shortlist
- identify the explicit watch insertion path that discovery should reuse
- confirm any API, serializer, or prompt boundaries that discovery must respect
- document any blocking gaps before implementation begins

## Proposed Approach

- scan backend asset, quote, and AI analysis entry points
- scan frontend monitored-set and asset-surface entry points
- prefer reuse of existing watch insertion flows over new mutation paths
- document the narrowest viable insertion path for deterministic discovery generation

## Validation Scenarios

- one market-scoped asset universe can be enumerated deterministically
- technical inputs required for the pre-filter are available or the exact gap is named
- a surfaced shortlist has an existing or obvious UI/API consumer
- discovery-to-watch insertion can reuse an explicit existing mutation path or the exact missing piece is documented

## Task Steps

1. Identify the current market-scoped asset universe source.
2. Confirm the available technical signal inputs for the approved pre-filter.
3. Confirm the current surfaces that can consume a discovery shortlist.
4. Confirm the explicit watch insertion path discovery should reuse.
5. Document any architectural gaps or blockers before moving to rule design.

## Tests to Add or Update

- none required unless the scan reveals a small helper or adapter that needs direct coverage

## Commands to Run

- `cd backend && ruff check .`
- run targeted backend tests only if small discovery-support helpers are introduced
- `cd frontend && npm run typecheck` only if frontend-facing contracts are adjusted during the scan

## Exit Conditions

- market-scoped universe source documented
- technical-signal availability documented
- shortlist consumer surface documented
- watch insertion point documented
- blockers, if any, documented clearly

## Implementation Notes / What Was Done

To be filled during execution.

## Open Follow-Ups

- none
