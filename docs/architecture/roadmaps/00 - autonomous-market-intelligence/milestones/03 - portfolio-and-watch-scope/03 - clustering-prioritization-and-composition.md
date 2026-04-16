# 03 - Clustering, Prioritization, and Composition

## Purpose

Define how monitored-set context should compose asset-level context, continuity reuse, shared-event clustering, and portfolio-level prioritization without flattening away asset detail.

## Roadmap Milestone

Milestone 03 - Portfolio and Watch Scope

## Governing ADR

ADR-003 Context Scope Expansion: Asset, Portfolio, Watchlist

## Status

planned

## Owner

unassigned

## Branch

feat/autonomous/03-scope-expansion

## Dependencies

- 00 - milestone coordination.md
- 01 - monitored-set-consumers-and-insertion-points.md
- 02 - scope-contracts-and-watch-membership.md

## Required Prior References

- `docs/architecture/adrs/ADR-002-narrative-continuity-for-asset-context.md`
- `docs/architecture/adrs/ADR-003-context-scope-expansion-asset-portfolio-watchlist.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/01 - asset-context-expansion/03 - deduplication-ranking-and-context-pack-shape.md`

## Likely Files Touched

- backend/ai/*
- backend/markets/*
- backend/portfolios/*
- backend/tests/*
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/03 - portfolio-and-watch-scope/03 - clustering-prioritization-and-composition.md

## Entry Conditions

- scope contract and membership rules defined
- insertion point documented
- required prior references reviewed

## Background

Milestone 03 is valuable only if monitored-set output reduces duplicate noise without erasing which assets are actually implicated. This task defines the monitored-set composition rules before the implementation task writes code.

## Detailed Requirements

- define how asset-level context packs are reused before monitored-set composition
- define when shared events are eligible for clustering
- define how clustered events list affected assets and preserve per-asset relevance
- define deterministic monitored-set prioritization rules for:
  - multi-asset impact
  - portfolio weight when scope is `portfolio`, measured as percentage of total portfolio market value
  - recency
  - surviving asset-level ranking and continuity filters
- define when the system should keep separate items instead of forcing a cluster
- keep the output shape auditable and compact

## Proposed Approach

- compose monitored-set output from already selected asset-level items rather than rescoring raw provider payloads at portfolio level
- cluster only when overlap is obvious through dedupe keys, story families, or theme tags, and only when at least two monitored assets retain the event with per-asset relevance at or above `0.50`
- preserve unique asset-specific items alongside clustered shared events
- keep continuity asset-bounded first, then compose the monitored-set view
- define one monitored-set output shape that can serve both portfolio and watch consumers
- preserve drill-down by returning compact implicated-asset summaries plus stable asset identifiers; full asset detail should be fetched through the existing `asset` scope path instead of expanding full detail inline

## Validation Scenarios

- one macro story affecting several monitored assets appears once with affected assets listed only when at least two implicated assets cross the `0.50` relevance floor
- one asset-specific earnings item remains asset-specific instead of being flattened into a cluster
- a larger portfolio position can outrank a smaller one when both share comparable event strength, using percentage of total portfolio market value
- weak or ambiguous overlap does not force clustering
- monitored-set output still allows drill-down to implicated assets through stable IDs and asset-scope reuse

## Task Steps

1. Define the monitored-set composition order from asset-level context selection through final summary shape.
2. Define cluster eligibility and rejection rules.
3. Define deterministic prioritization rules for portfolio and watch scope.
4. Define the monitored-set output shape, including clustered shared events and unique asset-level items.
5. Identify the minimum regression and validation tests needed for clustering and prioritization behavior.

## Tests to Add or Update

- clustering eligibility tests
- prioritization tests for multi-asset and portfolio-weighted cases
- regression tests preserving unique asset-specific items
- prompt-shape or serializer tests for monitored-set output structure

## Commands to Run

- `cd backend && ruff check .`
- run affected backend tests around context selection, continuity reuse, and monitored-set composition

## Exit Conditions

- monitored-set composition order is explicit
- clustering and prioritization rules are deterministic
- asset-level detail preservation is explicit
- implementation can proceed without rediscovering composition semantics

## Implementation Notes / What Was Done

Not started.

## Open Follow-Ups

- confirm whether monitored-set summaries need separate caps for clustered items and unique asset items after the first prompt-budget pass
