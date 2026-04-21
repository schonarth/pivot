# 01 - Trajectory Insertion Point and Signal Source Scan

## Purpose

Identify the narrowest correct insertion point for sentiment trajectory and confirm the exact short-window inputs available before defining scoring or persistence.

## Roadmap Milestone

Milestone 04 - Sentiment Trajectory

## Governing SPEC

SPEC-004 Sentiment Trajectory and Narrative State

## Status

done

## Owner

GPT-5.4 / implementation

## Branch

feat/autonomous/04-sentiment-trajectory

## Dependencies

- 00 - milestone coordination.md

## Required Prior References

- `docs/specs/SPEC-002-narrative-continuity-for-asset-context.md`
- `docs/specs/SPEC-003-context-scope-expansion-asset-portfolio-watchlist.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/02 - temporal-narrative-continuity/01 - continuity-insertion-point-and-retained-artifact-scan.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/02 - temporal-narrative-continuity/02 - retention-labeling-and-persistence-shape.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/02 - temporal-narrative-continuity/03 - prompt-continuity-section-and-ingestion-sentiment.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/03 - portfolio-and-watch-scope/01 - monitored-set-consumers-and-insertion-points.md`

## Likely Files Touched

- backend/ai/*
- backend/markets/*
- backend/mcp/*
- backend/tests/*
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/04 - sentiment-trajectory/01 - trajectory-insertion-point-and-signal-source-scan.md

## Entry Conditions

- milestone coordination reviewed
- SPEC-004 reviewed
- Milestone 02 continuity retention and prompt-shape files reviewed

## Background

SPEC-004 only works if trajectory reuses retained selected items and stored per-item sentiment instead of creating a parallel historical system. This task exists to confirm the live insertion point and signal source before any deterministic state rules are written.

The current repo scan suggests monitored-set surfaces now exist in code, including scope-level analysis, watch membership, and portfolio/watch summary consumers. This task should treat monitored-set readiness as something to verify concretely in the current codebase, not as an assumed gap from earlier milestone notes.

## Detailed Requirements

- identify the current code path where retained selected items and stored per-item sentiment first coexist
- identify the narrowest safe insertion point for trajectory computation
- confirm whether the same insertion point can support both:
  - `asset`
  - monitored-set consumers from Milestone 03 when implementation-ready
- verify the currently implemented monitored-set producer and consumer surfaces, including any portfolio/watch summary UI and backend service path already present in the repo
- identify all required input fields for deterministic trajectory:
  - item identity
  - asset identity
  - theme tags
  - base sentiment label
  - timestamp ordering
  - continuity labels if already present
- call out any missing persisted fields or coupling risks that would block implementation
- do not define scoring thresholds in this task

## Proposed Approach

- trace from the current asset analysis producer path backward into retained-item retrieval
- confirm the short-window source of truth before any prompt assembly or explanation step
- treat monitored-set reuse as additive only if the same retained-item contract can serve it cleanly
- document gaps separately from solutions so later tasks stay narrow

## Validation Scenarios

- an implementation agent should know exactly where trajectory belongs after reading this file
- the file should say whether trajectory can be computed fully from existing retained items and stored sentiment labels
- any missing theme-tag quality or timestamp-ordering gaps should be explicit
- the file should state clearly whether monitored-set surfaces are implementation-ready now, rather than inheriting stale assumptions from earlier milestone notes
- the insertion point should preserve the context-selection versus reasoning boundary

## Task Steps

1. Review the required prior references.
2. Trace the current retained-item and sentiment-label flow through the shared analysis path.
3. Verify the current monitored-set producer and consumer surfaces in backend and frontend code.
4. Identify the narrowest safe insertion point for trajectory computation.
5. Confirm which required trajectory inputs already exist and which do not.
6. Document coupling risks, missing fields, and monitored-set reuse constraints.

## Tests to Add or Update

- add or update smoke coverage around the chosen insertion point once implementation begins
- preserve existing asset-analysis behavior while trajectory is absent or partially wired

## Commands to Run

- `cd backend && ruff check .`
- run affected backend tests around AI analysis, retained items, and sentiment storage

## Exit Conditions

- insertion point identified
- current signal sources identified
- missing inputs or coupling risks documented
- later tasks can define scoring without rediscovering the pipeline

## Implementation Notes / What Was Done

Completed trajectory insertion-point validation and implementation alignment.

What was done:

- confirmed `AIService.analyze_asset` as the narrow asset-analysis insertion point
- confirmed `AIService.analyze_scope` as the monitored-set reuse point
- verified retained selected items and per-item sentiment labels already coexist in the shared context pack
- verified monitored-set consumers were implementation-ready and could reuse the same trajectory contract without a separate scoring path
- identified `asset_symbol`, `provenance`, `sentiment_score`, `published_at`, and existing continuity labels as the live input surface for deterministic trajectory

Monitored-set status:

- implementation-ready
- reused the same trajectory contract from the shared analysis path

## Open Follow-Ups

- none
