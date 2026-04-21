# 02 - Retention, Labeling, and Persistence Shape

## Purpose

Define the bounded retention rules, continuity labels, and compact persistence shape required to implement SPEC-002 without creating a broad narrative-history system.

## Roadmap Milestone

Milestone 02 - Temporal Narrative Continuity

## Governing SPEC

SPEC-002 Narrative Continuity for Asset Context

## Status

done

## Owner

GPT-5.4 / implementation

## Branch

feat/autonomous/02-temporal-continuity

## Date Started

2026-04-16

## Date Completed

2026-04-16

## Dependencies

- 00 - milestone coordination.md
- 01 - continuity-insertion-point-and-retained-artifact-scan.md

## Required Prior References

- `docs/specs/SPEC-002-narrative-continuity-for-asset-context.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces/02 - shared-vocabulary-and-interface-contracts.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces/03 - current-consumers-and-storage-touchpoints.md`

## Likely Files Touched

- backend/ai/*
- backend/markets/*
- backend/*/migrations/*
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/02 - temporal-narrative-continuity/02 - retention-labeling-and-persistence-shape.md

## Entry Conditions

- insertion point documented
- retained artifact candidate documented
- SPEC-002 retention and state-label decisions reviewed

## Background

Milestone 02 adds short-memory continuity only if retention remains explicit and bounded. This task exists to prevent accidental overreach into long-lived narrative storage or vague heuristic state. The continuity layer needs a compact retained unit, a hard-bounded lookback window, and deterministic labeling rules.

## Detailed Requirements

- define the exact continuity retention window and configuration shape
- define the fields needed on the retained continuity unit
- define deterministic labeling rules for:
  - `new`
  - `continuing`
  - `shifted`
- define what constitutes continuity identity and what constitutes a meaningful shift
- define what is persisted and what remains transient
- keep the milestone inside SPEC-002 bounds:
  - no full fact versioning
  - no long-lived narrative state tables
  - no replay-oriented raw prompt storage

## Proposed Approach

- start from SPEC-002 defaults:
  - target `5` days
  - allowed range `3-7` days
- prefer a compact additive artifact if existing `NewsItem` rows alone are not enough to represent prior selected items
- keep label computation deterministic before any LLM explanation
- define retention and cleanup behavior up front so implementation does not drift

## Validation Scenarios

- an implementation agent should be able to classify one current item as `new`, `continuing`, or `shifted` without consulting the LLM
- older items outside the window should be clearly excluded
- the design should stay explainable to operators and reviewers
- storage should remain materially smaller than a narrative-history system

## Task Steps

1. Define the continuity retention window and configuration defaults.
2. Define the retained continuity unit fields and how identity is derived.
3. Define deterministic label rules for `new`, `continuing`, and `shifted`.
4. Define what persistence is allowed and what remains transient.
5. Document retention cleanup or exclusion behavior for items outside the window.

## Tests to Add or Update

- unit tests for label classification
- unit tests for retention-window exclusion
- regression tests preserving Milestone 01 context-pack behavior when prior retained items are absent

## Commands to Run

- backend lint
- affected backend tests for continuity retention and labeling

## Exit Conditions

- retention rules explicit
- continuity unit explicit
- labels explicit
- persistence boundary explicit

## Implementation Notes / What Was Done

Defined a 5-day lookback window, deterministic `new` / `continuing` / `shifted` labeling, and compact persistence through existing `NewsItem` rows plus forward-only sentiment scores.

## Open Follow-Ups

- none
