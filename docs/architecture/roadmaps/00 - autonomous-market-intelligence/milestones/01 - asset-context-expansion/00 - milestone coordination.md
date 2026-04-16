# 00 - Milestone Coordination

## Purpose

Coordinate Milestone 01 execution so asset analysis gains broader, deterministic news context without expanding into narrative memory, recommendations, or autonomous behavior.

## Roadmap Milestone

Milestone 01 - Asset Context Expansion

## Governing ADR

ADR-001 Open News Context Expansion

## Status

planned

## Owner

unassigned

## Branch

feat/autonomous/01-asset-context

## Date Started

not started

## Date Completed

not started

## Dependencies

- Milestone 00 baseline work complete

## Likely Files Touched

- docs/architecture/adrs/ADR-001-open-news-context-expansion.md
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/roadmap.md
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/01 - asset-context-expansion/*
- backend/*
- frontend/*

## Entry Conditions

- roadmap reviewed
- ADR-001 reviewed
- Milestone 00 core outputs are complete enough to unblock Milestone 01:
  - boundary decision and current-state scan
  - shared vocabulary and interface contracts
  - current consumers and storage touchpoints
- baseline interfaces understood well enough to avoid mixing context, reasoning, and execution concerns

## Task Steps

1. Review ADR-001 and extract only in-scope work.
2. Quickly scan the codebase for the current asset analysis, news retrieval, and prompt assembly path.
3. Execute the milestone task files in order.
4. Keep the milestone scoped to compact asset context packs only.
5. Exclude narrative memory, strategy logic, and portfolio aggregation from implementation.
6. Prepare milestone-end smoke and integration verification for UAT.

## Tests to Add or Update

- milestone-level smoke coverage for the new context-building path
- regression coverage for the current asset analysis consumer
- representative validation scenarios for assets affected by macro or sector news without symbol mentions

## Commands to Run

- backend lint
- frontend typecheck if frontend files are touched
- affected backend and frontend tests
- milestone-end integration tests

## Exit Conditions

- asset analysis can consume a compact broader context pack
- context items are tagged by provenance bucket
- prompt budget remains explicit and bounded
- milestone remains user-releaseable

## Implementation Notes / What Was Done

Planned coordination file only.

## Open Follow-Ups

- confirm representative validation assets after scanning the seeded asset set
