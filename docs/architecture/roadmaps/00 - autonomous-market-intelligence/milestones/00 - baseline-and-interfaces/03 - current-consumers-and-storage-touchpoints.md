# 03 - Current Consumers and Storage Touchpoints

## Purpose

Map current consumers and likely storage touchpoints so Milestone 01 can integrate with the right parts of the system and avoid duplicate structures.

## Roadmap Milestone

Milestone 00 - Baseline and Interfaces

## Governing ADR

Roadmap-only planning task for Milestone 00 baseline work.

## Status

planned

## Owner

unassigned

## Branch

feat/autonomous/00-baseline

## Date Started

not started

## Date Completed

not started

## Dependencies

- 00 - milestone coordination.md
- 01 - boundary-decision-and-current-state-scan.md
- 02 - shared-vocabulary-and-interface-contracts.md

## Likely Files Touched

- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces/03 - current-consumers-and-storage-touchpoints.md
- backend/*
- frontend/*

## Entry Conditions

- baseline vocabulary drafted
- current-state scan drafted

## Background

Milestone 01 should improve the current asset-analysis consumer first, but later milestones will likely expand to portfolio, watched assets, and strategy validation. Before building anything, the project needs a clear view of who consumes context today and which data should remain transient versus which data may later justify storage.

## Detailed Requirements

- identify the current consumer that Milestone 01 is improving
- list the near-term roadmap consumers in dependency order where possible
- identify likely storage touchpoints for:
  - news metadata
  - context artifacts
  - technical signals
  - analysis outputs
- distinguish between:
  - data that should likely stay transient in early milestones
  - data that may justify persistence later
- identify risks of creating duplicate storage or duplicate prompt-building paths
- avoid introducing schemas or migrations in this task

## Proposed Approach

- derive the current consumer from the actual implementation path, not only from the roadmap
- list future consumers only where they materially affect architectural choices
- frame storage notes as touchpoints and boundaries, not final schema design
- prefer a simple table or bullet map that later tasks can reuse directly

## Validation Scenarios

- a Milestone 01 implementation task should be able to identify its current consumer immediately from this file
- a later portfolio or watch milestone should be able to see whether it is expected to reuse or extend the same context path
- if stored news artifacts are not yet justified, this file should say so explicitly to prevent accidental overbuilding
- if duplicate storage paths are a likely risk, they should be called out concretely enough to guide code review

## Task Steps

1. Identify the current consumer for asset-level analysis.
2. List probable near-term consumers:
   - asset analysis
   - portfolio monitoring
   - watched-assets monitoring
   - strategy validation
3. Identify where context, analysis artifacts, news metadata, and technical signals likely belong if stored.
4. Note what should remain transient until later milestones prove persistent storage is needed.
5. Call out duplication risks if multiple milestones create separate storage or prompt-building paths.

## Tests to Add or Update

- docs-only baseline task
- no direct unit tests expected unless code changes are introduced to preserve current consumers

## Commands to Run

- if code is touched: run relevant lint, typecheck, and affected tests

## Exit Conditions

- current consumer is explicitly named
- likely future consumers are listed in roadmap terms
- likely storage touchpoints are documented with boundaries
- transient versus persistent data concerns are called out

## Implementation Notes / What Was Done

Not started.

## Open Follow-Ups

- see Deferred Improvements `002 - Persisted News Artifacts Beyond Prompt-Time Assembly`
