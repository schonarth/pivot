# 05 - Watch Handoff, Refinement, and Validation

## Purpose

Complete the explicit discovery-to-watch handoff, optional refined-shortlist reuse, and milestone-end validation so Milestone 06 ships as a coherent user-facing discovery feature rather than a raw ranking backend.

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
- 04 - discovery-implementation-and-release-readiness.md

## Required Prior References

- `docs/specs/SPEC-003-context-scope-expansion-asset-portfolio-watchlist.md`
- `docs/specs/SPEC-006-opportunity-discovery-pipeline.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/03 - portfolio-and-watch-scope/05 - portfolio-and-watch-ui-surface.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/03 - portfolio-and-watch-scope/06 - portfolio-and-watch-scope-ai-summary.md`

## Likely Files Touched

- backend/ai/*
- backend/mcp/*
- backend/tests/*
- frontend/src/*
- frontend/tests/*
- docs/reference/*
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/06 - opportunity-discovery/05 - watch-handoff-refinement-and-validation.md

## Entry Conditions

- deterministic discovery implemented
- chosen discovery consumer in place
- fallback and refined-cache contracts already in use

## Background

Milestone 06 is only fully useful if surfaced candidates can become watched assets without manual duplication and if optional refinement behaves honestly when users revisit discovery. This task finalizes those user-facing workflows and closes milestone validation.

## Detailed Requirements

- implement explicit watch insertion from surfaced discovery candidates if the current watch path is implementation-ready
- keep watch insertion user-visible and explicit
- preserve the rule that already-held assets are excluded from discovery even when watch handoff is enabled
- implement or finalize refined-shortlist cache reuse when discovery is reopened
- preserve deterministic shortlist ordering regardless of refined-cache state
- validate that users without API keys still get the same fallback-first experience
- document any discovery usage or validation tooling in general project documentation if new tools land
- if watch insertion cannot land cleanly, document the exact blocker rather than inventing a new watch mutation path

## Proposed Approach

- reuse the existing watch insertion mutation path rather than creating a discovery-only side effect
- keep refined-cache behavior scoped to the surfaced shortlist, not to broader candidate history
- validate the daily user loop explicitly:
  - scheduled shortlist exists
  - user opens discovery
  - fallback or refined view appears honestly
  - user can add a surfaced asset to watch explicitly

## Validation Scenarios

- surfaced candidates can be added to watch without duplicate manual entry
- already-held assets remain excluded from surfaced discovery candidates
- watch insertion is explicit and user-visible
- reopening the same shortlist within `24h` reuses refined output when valid
- changed shortlist or explicit refresh invalidates cached refinement
- no API key still yields the deterministic fallback experience

## Task Steps

1. Implement or finalize explicit watch insertion from surfaced candidates.
2. Implement or finalize refined-shortlist cache reuse and invalidation behavior.
3. Add or update regression coverage for watch handoff and refined-cache reuse.
4. Document any new user-facing usage or validation tooling if introduced.
5. Run lint, typecheck, affected tests, and milestone integration checks.
6. Prepare final handoff notes:
   - watch insertion status
   - refined-cache behavior
   - known limitations
   - whether deferred discovery-history or asset-universe expansion work should be revisited next

## Tests to Add or Update

- watch insertion regression tests
- regression tests proving held assets do not reappear in surfaced discovery output
- refined-cache reuse and invalidation tests
- frontend flow tests for discovery open and watch handoff if frontend is in scope
- milestone integration tests for discovery-to-watch behavior

## Commands to Run

- `cd backend && ruff check .`
- `cd backend && pytest`
- `cd frontend && npm run typecheck`
- run affected frontend tests if frontend code changes
- run milestone integration tests covering discovery-to-watch and refined-cache reuse

## Exit Conditions

- watch insertion works or is explicitly deferred with a concrete blocker
- refined-cache reuse is correct and honest
- fallback-only and refined flows are both validated
- tests pass
- milestone handoff notes are complete
- task file updated with actual implementation outcome

## Implementation Notes / What Was Done

Completed the discovery-to-watch handoff and validation slice:

- discovery view adds a surfaced asset to watch through the existing portfolio watch endpoint
- watch insertion remains explicit and user-visible
- refined shortlist reuse is available through the user-initiated refresh path
- deterministic ordering remains the source of truth regardless of refinement cache state
- frontend and backend tests cover the watch handoff path and discovery reuse behavior

## Open Follow-Ups

- none
