# 02 - Source Selection, Tagging, and Config Shape

## Purpose

Define how Milestone 01 selects broader asset context sources and how those sources are tagged and configured without introducing retrieval complexity.

## Roadmap Milestone

Milestone 01 - Asset Context Expansion

## Governing SPEC

SPEC-001 Open News Context Expansion

## Status

done

## Owner

GPT-5.4-Mini / implementation

## Branch

feat/autonomous/01-asset-context

## Date Started

2026-04-15

## Date Completed

2026-04-15

## Dependencies

- 00 - milestone coordination.md
- 01 - existing-pipeline-scan-and-insertion-point.md

## Required Prior References

- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces/02 - shared-vocabulary-and-interface-contracts.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces/03 - current-consumers-and-storage-touchpoints.md`

## Likely Files Touched

- backend/*
- docs/specs/SPEC-001-open-news-context-expansion.md
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/01 - asset-context-expansion/02 - source-selection-tagging-and-config-shape.md

## Entry Conditions

- insertion point identified
- current asset metadata sources reviewed
- required Milestone 00 references reviewed

## Background

SPEC-001 expands context selection from symbol-only headlines to a broader deterministic set of sources. This task turns that direction into an explicit source model for Milestone 01 so later implementation does not drift into ad hoc retrieval logic or broad, noisy prompt dumps.

## Detailed Requirements

- define the Milestone 01 source buckets explicitly:
  - symbol
  - company
  - sector
  - industry
  - macro
  - theme
- specify what project metadata should seed sector and industry lookup first
- specify fallback behavior when metadata is missing or incomplete
- define the tag vocabulary and minimum metadata each context item carries
- decide which thematic mappings belong in configuration versus code
- keep the design deterministic
- do not introduce temporal continuity, sentiment trajectory, recommendations, or strategy logic

## Proposed Approach

- start from the asset metadata already present in the repo and only add mappings where project data is insufficient
- keep the context-item shape minimal but stable enough for tests
- prefer configuration for thematic keyword mappings if that improves maintainability without forcing unnecessary infrastructure
- name the fallback order clearly so later tasks do not improvise it
- keep the tag set aligned exactly with SPEC-001 and the roadmap

## Validation Scenarios

- an asset with complete metadata should resolve source buckets without fallback
- an asset with missing sector or industry metadata should follow a documented fallback path
- a macro-only driver should still produce a tagged context item even when the symbol is absent from the headline
- a theme mapping should be explainable and testable rather than inferred opaquely

## Task Steps

1. Reuse the Milestone 00 vocabulary and storage boundaries as constraints.
2. Define the source buckets for Milestone 01:
   - symbol
   - company
   - sector
   - industry
   - macro
   - theme
3. Decide what project data should seed sector and industry lookup first.
4. Decide what should be configuration versus code for thematic keyword mappings.
5. Define the tag set and the minimum metadata each context item should carry in a way that matches the Milestone 00 interface contract.
6. Keep the design deterministic and compact.
7. Exclude temporal continuity and sentiment trajectory from this task.

## Tests to Add or Update

- unit tests for source bucket assignment
- smoke tests for tag generation
- edge-case tests for missing sector or industry metadata

## Commands to Run

- backend lint
- affected backend tests for source selection and tagging
- frontend typecheck if shared client contracts are touched

## Exit Conditions

- source bucket rules are explicit
- tag vocabulary is fixed for Milestone 01
- configuration shape is defined for thematic keyword mappings if needed
- missing-metadata fallback behavior is documented and testable

## Implementation Notes / What Was Done

Defined the Milestone 01 source model and tagging policy.

What was done:

- fixed the source buckets as `symbol`, `company`, `sector`, `industry`, `macro`, and `theme`
- established deterministic fallback behavior for incomplete metadata using existing asset data first, then explicit overrides
- defined the minimum context-item metadata needed for tagged asset analysis
- kept thematic mappings in code as a small versioned policy artifact instead of a database-backed structure

Open follow-ups:

- populate `ASSET_METADATA_OVERRIDES` only if a real seeded-data gap appears

## Open Follow-Ups

- choose the initial configuration file location if theme mappings are not kept inline
