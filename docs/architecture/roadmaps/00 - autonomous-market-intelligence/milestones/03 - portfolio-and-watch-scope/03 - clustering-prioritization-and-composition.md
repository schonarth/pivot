# 03 - Clustering, Prioritization, and Composition

## Purpose

Define how monitored-set context should compose asset-level context, continuity reuse, shared-event clustering, and portfolio-level prioritization without flattening away asset detail.

## Roadmap Milestone

Milestone 03 - Portfolio and Watch Scope

## Governing SPEC

SPEC-003 Context Scope Expansion: Asset, Portfolio, Watchlist

## Status

done

## Owner

GPT-5.4-Mini / implementation

## Branch

feat/autonomous/03-scope-expansion

## Date Started

2026-04-16

## Date Completed

2026-04-16

## Dependencies

- 00 - milestone coordination.md
- 01 - monitored-set-consumers-and-insertion-points.md
- 02 - scope-contracts-and-watch-membership.md

## Required Prior References

- `docs/specs/SPEC-002-narrative-continuity-for-asset-context.md`
- `docs/specs/SPEC-003-context-scope-expansion-asset-portfolio-watchlist.md`
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

- reuse already selected asset-level context packs as the only input to monitored-set composition; do not rescore raw provider payloads at portfolio or watch scope
- define when shared events are eligible for clustering:
  - overlap must be obvious through dedupe keys, story families, or theme tags
  - at least two monitored assets must retain the event with per-asset relevance at or above `0.50`
  - the shared event must still survive asset-level continuity filters for the participating assets
- define when shared events must remain separate:
  - only one monitored asset retains the item above the relevance floor
  - overlap is ambiguous or weak
  - the event is asset-specific even if the topic is broadly related
- define how clustered events list affected assets while preserving per-asset relevance, stable asset identifiers, and drill-down paths
- define deterministic monitored-set prioritization rules for:
  - multi-asset impact
  - portfolio weight when scope is `portfolio`, measured as percentage of total portfolio market value
  - recency
  - surviving asset-level ranking and continuity filters
- keep the output shape auditable and compact
- make the same composition rules reusable for both `portfolio` and `watch` scopes without introducing a second pipeline

## Proposed Approach

- select asset-level context first, apply continuity filters per asset, then compose the monitored set from the surviving items
- cluster only after the asset-level pass has produced overlapping survivors for at least two monitored assets
- prioritize clustered events by:
  - higher number of implicated assets
  - larger portfolio weight for portfolio scope
  - more recent `published_at` or equivalent event timestamp
  - stronger surviving asset-level rank after continuity reuse
- preserve unique asset-specific items alongside clustered shared events instead of flattening them into clusters
- define one monitored-set output shape that can serve both portfolio and watch consumers
- preserve drill-down by returning compact implicated-asset summaries plus stable asset identifiers; full asset detail should be fetched through the existing `asset` scope path instead of expanding full detail inline
- keep portfolio and watch ordering deterministic so equal inputs produce equal output ordering

## Validation Scenarios

- one macro story affecting several monitored assets appears once with affected assets listed only when at least two implicated assets cross the `0.50` relevance floor
- one asset-specific earnings item remains asset-specific instead of being flattened into a cluster
- a larger portfolio position can outrank a smaller one when both share comparable event strength, using percentage of total portfolio market value
- weak or ambiguous overlap does not force clustering
- monitored-set output still allows drill-down to implicated assets through stable IDs and asset-scope reuse
- portfolio and watch scopes produce the same monitored-set structure while preserving scope-specific ordering inputs

## Task Steps

1. Define the monitored-set composition order from asset-level context selection through final summary shape.
2. Define cluster eligibility and rejection rules.
3. Define deterministic prioritization rules for portfolio and watch scope.
4. Define the monitored-set output shape, including clustered shared events and unique asset-level items.
5. Identify the minimum regression and validation tests needed for clustering and prioritization behavior.
6. Record the handoff state directly in this task file so the next pass does not need to rediscover ownership or completion status.

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
- Owner, Status, Date Started, Date Completed, and handoff notes are filled in this file

## Implementation Notes / What Was Done

Defined the monitored-set composition contract for Milestone 03. Asset-level context packs are reused first, then clustered only when overlap is obvious and at least two monitored assets keep the item at or above the `0.50` relevance floor. Separate items are preserved when overlap is weak, ambiguous, or asset-specific. Prioritization is deterministic across portfolio and watch scopes, with portfolio scope using portfolio-weight percentage as an ordering input. The monitored-set shape stays compact, auditable, and drill-down friendly through stable asset IDs and compact implicated-asset summaries.

## Open Follow-Ups

- confirm whether monitored-set summaries need separate caps for clustered items and unique asset items after the first prompt-budget pass
- update the execution model to make pre-handoff Owner completion part of the default task flow
