# 00 - Milestone Coordination

## Purpose

Coordinate Milestone 06 execution so the system can surface a bounded daily shortlist of assets worth watching from the current market universe without turning discovery into bulk LLM scanning or autonomous execution.

## Roadmap Milestone

Milestone 06 - Opportunity Discovery

## Governing ADR

ADR-006 Opportunity Discovery Pipeline

## Status

done

## Owner

GPT-5.4 / coordination

## Date Started

2026-04-19

## Date Completed

2026-04-19

## Branch

feat/autonomous/06-opportunity-discovery

## Dependencies

- ADR-006 approved
- required references:
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/roadmap.md`
  - `docs/architecture/execution/milestone-delivery-execution-model.md`
  - `docs/architecture/adrs/ADR-001-open-news-context-expansion.md`
  - `docs/architecture/adrs/ADR-002-narrative-continuity-for-asset-context.md`
  - `docs/architecture/adrs/ADR-003-context-scope-expansion-asset-portfolio-watchlist.md`
  - `docs/architecture/adrs/ADR-004-sentiment-trajectory-and-narrative-state.md`
  - `docs/architecture/adrs/ADR-005-divergence-reasoning-for-market-analysis.md`
  - `docs/architecture/adrs/ADR-006-opportunity-discovery-pipeline.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/03 - portfolio-and-watch-scope/04 - implementation-validation-and-release-readiness.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/03 - portfolio-and-watch-scope/05 - portfolio-and-watch-ui-surface.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/03 - portfolio-and-watch-scope/06 - portfolio-and-watch-scope-ai-summary.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/04 - sentiment-trajectory/04 - implementation-validation-and-release-readiness.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/05 - counterfactual-and-divergence-reasoning/04 - asset-divergence-implementation-and-release-readiness.md`
  - `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/05 - counterfactual-and-divergence-reasoning/05 - monitored-set-extension-cli-and-validation.md`

## Likely Files Touched

- docs/architecture/adrs/ADR-006-opportunity-discovery-pipeline.md
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/06 - opportunity-discovery/*
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/deferred-improvements.md
- backend/ai/*
- backend/markets/*
- backend/mcp/*
- backend/tests/*
- frontend/src/*
- frontend/tests/*
- docs/reference/*

## Entry Conditions

- roadmap reviewed
- milestone delivery execution model reviewed
- ADR-006 reviewed
- Milestone 03 watch and monitored-set files reviewed as normative inputs for watch handoff and UI reuse
- Milestone 04 trajectory files reviewed as normative inputs for bounded context support
- Milestone 05 divergence files reviewed as normative inputs for optional ranking support and cache honesty

## Task Steps

1. Read the roadmap, milestone delivery execution model, ADR-006, and required prior references before implementation.
2. Confirm the current source of truth for market-scoped asset universes, technical data availability, discovery consumers, and watch insertion points.
3. Execute Milestone 06 task files in order.
4. Keep scheduled discovery deterministic and non-LLM.
5. Use all current stored assets in one explicit market at a time as the first eligible universe.
6. Keep the technical pre-filter assertive and small:
   - liquidity floor
   - trend intact
   - breakout or near-breakout confirmation
7. Cap the deterministic screen to `20` survivors and the surfaced shortlist to `5`.
8. Rank survivors with a small blended deterministic score using technical setup quality, breakout quality, bounded context support, and freshness.
9. Keep the non-LLM fallback useful by emitting canonical structured records plus one deterministic one-line reason per surfaced asset.
10. Allow LLM refinement only when the user actively opens discovery and LLM access is available; never spend tokens only because a schedule fired.
11. Cache refined shortlist output only as an optimization:
   - latest refined shortlist only
   - tied to deterministic shortlist fingerprint
   - hard TTL `24h`
12. Keep discovery separate from execution:
   - no auto-buy behavior
   - no hidden watch mutation
   - no user-invisible ranking model drift
13. Make the final milestone handoff explicit about:
   - whether watch insertion from discovery is implemented end to end
   - whether deterministic fallback and optional refinement both ship cleanly
   - what exact cache invalidation rules landed
   - whether the next step should proceed directly to Milestone 07 or detour to discovery-history or asset-universe expansion follow-up work

## Tests to Add or Update

- deterministic pre-filter eligibility tests
- deterministic ranking tests covering shortlist ordering
- regression tests for non-LLM fallback output shape
- cache reuse and invalidation tests for refined shortlist output
- watch insertion regression tests if discovery-to-watch handoff lands
- frontend tests for surfaced shortlist rendering and optional refined reuse if frontend changes land

## Commands to Run

- `cd backend && ruff check .`
- `cd backend && pytest`
- `cd frontend && npm run typecheck`
- run affected frontend tests if frontend code changes
- run milestone integration tests covering discovery generation, watch insertion, and refined-cache reuse

## Exit Conditions

- market-scoped deterministic discovery works end to end
- scheduled runs stay non-LLM
- surfaced shortlist is capped, auditable, and useful without refinement
- optional refinement only happens when the user opens discovery with LLM access available
- refined cache behavior is explicit and correct
- watch insertion is either implemented or explicitly deferred without ambiguity
- milestone remains user-releaseable

## Implementation Notes / What Was Done

Completed Milestone 06 setup.

What was done:

- reviewed the roadmap, execution model, ADR-006, and Milestone 03 to 05 handoff files before creating the milestone scaffold
- created the Milestone 06 folder and task sequence for universe and insertion-point scan, deterministic pre-filter and ranking contract, fallback and refinement contract, implementation slice, and watch handoff plus validation
- aligned the scaffold with the approved Milestone 06 decisions:
  - all stored assets in one explicit market at a time
  - deterministic non-LLM scheduled preselection
  - liquidity plus trend plus breakout confirmation pre-filter
  - `20` survivors and `5` surfaced candidates
  - small blended deterministic ranking score
  - structured fallback plus deterministic one-line reason
  - optional refinement only when discovery is actively opened
  - latest-only refined cache tied to shortlist fingerprint with `24h` TTL

## Open Follow-Ups

- none
