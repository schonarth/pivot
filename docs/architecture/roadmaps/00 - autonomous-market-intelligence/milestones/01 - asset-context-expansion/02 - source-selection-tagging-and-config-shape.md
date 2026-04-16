# 02 - Source Selection, Tagging, and Config Shape

## Purpose

Define how Milestone 01 selects broader asset context sources and how those sources are tagged and configured without introducing retrieval complexity.

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

- 00 - milestone coordination.md
- 01 - existing-pipeline-scan-and-insertion-point.md

## Likely Files Touched

- backend/*
- docs/architecture/adrs/ADR-001-open-news-context-expansion.md
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/01 - asset-context-expansion/02 - source-selection-tagging-and-config-shape.md

## Entry Conditions

- insertion point identified
- current asset metadata sources reviewed

## Background

ADR-001 expands context selection from symbol-only headlines to a broader deterministic set of sources. This task turns that direction into an explicit source model for Milestone 01 so later implementation does not drift into ad hoc retrieval logic or broad, noisy prompt dumps.

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
- keep the tag set aligned exactly with ADR-001 and the roadmap

## Validation Scenarios

- an asset with complete metadata should resolve source buckets without fallback
- an asset with missing sector or industry metadata should follow a documented fallback path
- a macro-only driver should still produce a tagged context item even when the symbol is absent from the headline
- a theme mapping should be explainable and testable rather than inferred opaquely

## Task Steps

1. Define the source buckets for Milestone 01:
   - symbol
   - company
   - sector
   - industry
   - macro
   - theme
2. Decide what project data should seed sector and industry lookup first.
3. Decide what should be configuration versus code for thematic keyword mappings.
4. Define the tag set and the minimum metadata each context item should carry.
5. Keep the design deterministic and compact.
6. Exclude temporal continuity and sentiment trajectory from this task.

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

Not started.

## Open Follow-Ups

- choose the initial configuration file location if theme mappings are not kept inline
