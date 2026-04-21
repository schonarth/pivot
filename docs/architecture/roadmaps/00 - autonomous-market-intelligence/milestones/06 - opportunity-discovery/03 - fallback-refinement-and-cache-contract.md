# 03 - Fallback, Refinement, and Cache Contract

## Purpose

Define the non-LLM discovery output shape, the exact trigger for optional refinement, and the refined-cache lifecycle so Milestone 06 remains useful without an API key while still avoiding background token spend.

## Roadmap Milestone

Milestone 06 - Opportunity Discovery

## Governing SPEC

SPEC-006 Opportunity Discovery Pipeline

## Status

done

## Owner

GPT-5.4 / implementation

## Date Started

2026-04-19

## Date Completed

2026-04-19

## Branch

feat/autonomous/06-opportunity-discovery

## Dependencies

- 00 - milestone coordination.md
- 01 - discovery-universe-and-insertion-point-scan.md
- 02 - deterministic-prefilter-and-ranking-rules.md

## Required Prior References

- `docs/specs/SPEC-003-context-scope-expansion-asset-portfolio-watchlist.md`
- `docs/specs/SPEC-006-opportunity-discovery-pipeline.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/03 - portfolio-and-watch-scope/05 - portfolio-and-watch-ui-surface.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/05 - counterfactual-and-divergence-reasoning/03 - output-shape-presentation-and-ui-disclosure.md`

## Likely Files Touched

- backend/ai/*
- backend/mcp/*
- backend/tests/*
- frontend/src/*
- frontend/tests/*
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/06 - opportunity-discovery/03 - fallback-refinement-and-cache-contract.md

## Entry Conditions

- deterministic pre-filter and ranking rules documented
- SPEC-006 fallback and refinement boundaries reviewed

## Background

Milestone 06 must work in two honest modes: deterministic fallback when no LLM access is available, and optional refinement only when the user actively opens discovery and LLM access is configured. This task defines the exact payload and cache behavior for both modes before end-to-end implementation begins.

## Detailed Requirements

- define the canonical structured fallback discovery record
- define the deterministic one-line reason format
- define when discovery-open is treated as the explicit user action authorizing optional refinement
- define whether refinement runs for the whole surfaced shortlist or only for candidates lacking cache
- define the refined-cache key and shortlist fingerprint linkage
- define TTL and invalidation behavior:
  - latest refined shortlist only
  - fingerprint match required
  - hard TTL `24h`
- keep cached refinement as an optimization only, never as the source of shortlist truth

## Proposed Approach

- keep the structured fallback record canonical for both modes
- treat deterministic shortlist generation and optional refinement as separate phases in the consumer flow
- cache at the shortlist level rather than per-asset if that keeps invalidation simpler and more honest
- define exactly what user-visible state appears when no API key exists, when cache is reused, and when a fresh refinement is triggered

## Validation Scenarios

- discovery works without any LLM access
- opening discovery with LLM access available can refine the surfaced shortlist without changing deterministic ordering
- reopening discovery within `24h` with the same shortlist reuses refined cache
- shortlist membership or material ordering change invalidates prior cache
- explicit user refresh bypasses or replaces cached refinement

## Task Steps

1. Define the canonical fallback record shape and one-line reason template inputs.
2. Define the exact user action that authorizes optional refinement.
3. Define shortlist-level cache key, fingerprint, TTL, and invalidation rules.
4. Define the consumer states for fallback-only, cached refinement, and fresh refinement.
5. Identify tests needed to lock the contract before implementation.

## Tests to Add or Update

- serializer or payload-shape tests for fallback records
- deterministic one-line reason tests
- cache reuse and invalidation regression tests
- frontend state tests for fallback-only vs refined rendering if frontend is in scope

## Commands to Run

- `cd backend && ruff check .`
- run affected backend tests around serializers, cache helpers, and refinement gating
- `cd frontend && npm run typecheck` if frontend consumer contracts change

## Exit Conditions

- fallback shape explicit
- refinement trigger explicit
- refined-cache lifecycle explicit
- consumer states explicit
- required regression tests identified

## Implementation Notes / What Was Done

Implemented the fallback and refinement contract in the discovery service and UI:

- canonical fallback output is the structured shortlist record
- each item always includes a deterministic one-line reason
- refinement is only requested when the user opens discovery and AI access is available
- refined results are cached by deterministic shortlist fingerprint
- cache is latest-only per market and user
- cache TTL is `24h`
- explicit refresh bypasses the cached refinement path

## Open Follow-Ups

- none
