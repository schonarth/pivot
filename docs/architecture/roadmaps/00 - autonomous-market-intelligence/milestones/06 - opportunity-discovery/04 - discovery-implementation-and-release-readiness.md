# 04 - Discovery Implementation and Release Readiness

## Purpose

Implement deterministic market-scoped discovery end to end, ship the non-LLM fallback output, and validate the first complete Milestone 06 slice without crossing into autonomous execution.

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
- 03 - fallback-refinement-and-cache-contract.md

## Required Prior References

- `docs/specs/SPEC-006-opportunity-discovery-pipeline.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/03 - portfolio-and-watch-scope/04 - implementation-validation-and-release-readiness.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/05 - counterfactual-and-divergence-reasoning/04 - asset-divergence-implementation-and-release-readiness.md`

## Likely Files Touched

- backend/ai/*
- backend/markets/*
- backend/mcp/*
- backend/tests/*
- frontend/src/*
- frontend/tests/*
- docs/reference/*
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/06 - opportunity-discovery/04 - discovery-implementation-and-release-readiness.md

## Entry Conditions

- insertion points documented
- deterministic rules finalized
- fallback, refinement, and cache contract finalized

## Background

This is the first complete Milestone 06 implementation slice. It applies the deterministic discovery pipeline to one market-scoped asset universe with already-held assets excluded, emits the capped shortlist with useful fallback explanations, and validates the user-visible discovery experience before optional watch insertion and broader polish work continue.

## Detailed Requirements

- implement deterministic market-scoped discovery using the approved eligible universe
- exclude assets already held in any user portfolio before technical filtering begins
- implement the exact small assertive pre-filter
- implement deterministic `20 -> 5` reduction and ranking
- expose the canonical structured fallback record and one-line reason for each surfaced asset
- preserve honest behavior when no LLM access is available
- if optional refinement lands in this slice, keep it gated to user-open only and keep ordering unchanged
- keep discovery inside SPEC-006 scope:
  - no auto-buy behavior
  - no hidden watch mutation
  - no scheduled LLM refinement
  - no broad discovery-history feature
- prepare release-readiness notes with user-visible behavior and known limits

## Proposed Approach

- add deterministic backend coverage before broad UI wiring where practical
- land the smallest complete discovery flow first, even if watch insertion or refined caching remains for the next task
- keep ordering and explanation traceable from stored inputs
- validate one market-scoped example end to end before widening any reuse

## Validation Scenarios

- one market can produce a deterministic capped shortlist
- assets already held in any user portfolio do not appear in discovery output
- the same input universe produces stable shortlist ordering
- users without API keys still see useful fallback reasons
- users do not trigger LLM spend unless they actively open the discovery experience
- discovery output does not mutate watch membership on its own

## Task Steps

1. Implement deterministic discovery generation for one market-scoped asset universe with held-asset exclusion.
2. Add or update regression coverage for held-asset exclusion, filters, ranking, and fallback output.
3. Expose the surfaced shortlist to the chosen user-facing consumer.
4. Validate fallback-only behavior with no LLM access.
5. Run lint, typecheck, affected tests, and milestone integration checks.
6. Prepare UAT notes:
   - user-visible discovery behavior
   - what makes a candidate surface
   - what still requires explicit user action

## Tests to Add or Update

- deterministic discovery generation tests
- held-asset exclusion regression tests
- shortlist-order regression tests
- fallback output tests
- integration tests for the selected discovery consumer
- frontend rendering tests if frontend is in scope

## Commands to Run

- `cd backend && ruff check .`
- `cd backend && pytest`
- `cd frontend && npm run typecheck`
- run affected frontend tests if frontend code changes
- run milestone integration tests covering discovery output consumption

## Exit Conditions

- deterministic discovery works end to end for at least one market
- fallback output is useful without LLM access
- scheduled runs remain non-LLM
- ordering is stable and auditable
- tests pass
- release-readiness notes are ready
- task file updated with actual implementation outcome

## Implementation Notes / What Was Done

Implemented the end-to-end discovery slice:

- backend discovery service for market-scoped deterministic screening
- authenticated discovery API at `/api/ai/discovery/`
- optional refinement gate tied to explicit user discovery open
- frontend discovery page with shortlist rendering and watch action
- explicit watch insertion through the existing portfolio watch mutation
- regression tests for shortlist output, ordering, and refined-cache reuse

## Open Follow-Ups

- none
