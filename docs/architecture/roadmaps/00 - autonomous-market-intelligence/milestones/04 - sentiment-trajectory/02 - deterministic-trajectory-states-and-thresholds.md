# 02 - Deterministic Trajectory States and Thresholds

## Purpose

Define the deterministic rules that map bounded recent sentiment inputs into `improving`, `deteriorating`, `conflicting`, and `reversal`.

## Roadmap Milestone

Milestone 04 - Sentiment Trajectory

## Governing ADR

ADR-004 Sentiment Trajectory and Narrative State

## Status

planned

## Owner

unassigned

## Branch

feat/autonomous/04-sentiment-trajectory

## Dependencies

- 00 - milestone coordination.md
- 01 - trajectory-insertion-point-and-signal-source-scan.md

## Required Prior References

- `docs/architecture/adrs/ADR-004-sentiment-trajectory-and-narrative-state.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/02 - temporal-narrative-continuity/02 - retention-labeling-and-persistence-shape.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/02 - temporal-narrative-continuity/03 - prompt-continuity-section-and-ingestion-sentiment.md`

## Likely Files Touched

- backend/ai/*
- backend/tests/*
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/04 - sentiment-trajectory/02 - deterministic-trajectory-states-and-thresholds.md

## Entry Conditions

- insertion point documented
- available input fields documented
- ADR-004 trajectory-state requirements reviewed

## Background

Milestone 04 is only auditable if the underlying state is determined by explicit rules before the LLM explains it. This task defines those rules while keeping the state model small and reviewable.

## Detailed Requirements

- define the deterministic scoring inputs and ordering rules
- define the default short-window weighting rules
- define the minimum evidence required for each state:
  - `improving`
  - `deteriorating`
  - `conflicting`
  - `reversal`
- define tie-breaking and indeterminate cases
- define when neutral items dampen, preserve, or do not affect state
- define whether continuity labels such as `new`, `continuing`, or `shifted` affect scoring or explanation only
- do not add a fifth canonical trajectory state for weak or unclear evidence
- define the deterministic no-state outcome when evidence is insufficient or non-directional
- keep the rules bounded to the short continuity window
- do not rely on the LLM to decide the state

## Proposed Approach

- map `positive`, `neutral`, and `negative` into a small ordinal scoring model
- score ordered retained items inside the bounded window with explicit recency weighting
- treat `conflicting` and `reversal` as first-class states with explicit thresholds instead of fallback prose
- define an explicit no-state rule when evidence is too weak or not directionally meaningful
- allow user-facing consumers to optionally render lightweight fallback language such as `no clear direction` or `not enough recent input` only when it adds explanatory value; otherwise omit the trajectory entry to avoid noise
- treat fading or disappearing signal as absence of current directional state in Milestone 04, not as a new canonical `story ended` state

## Validation Scenarios

- recent negative items following earlier positive items can produce `reversal` when the flip is material
- mixed recent positive and negative items with no dominant move produce `conflicting`
- mostly improving recent tone with bounded weak noise still produces `improving`
- old items outside the window do not affect the state
- weak, sparse, or mostly neutral evidence yields no trajectory state rather than a forced classification
- the same input sequence always yields the same state

## Task Steps

1. Define the trajectory scoring inputs and their ordering.
2. Define recency weighting and minimum evidence rules.
3. Define state thresholds and tie-breaking behavior.
4. Define the no-state outcome for weak or unclear evidence.
5. Define how neutral items and continuity labels affect the result.
6. Identify the minimum unit tests needed for each state and edge case.

## Tests to Add or Update

- unit tests for all four required trajectory states
- unit tests for weak-evidence and tie cases
- retention-window tests proving expired items do not affect scoring

## Commands to Run

- `cd backend && ruff check .`
- run affected backend tests around trajectory scoring

## Exit Conditions

- scoring inputs explicit
- state rules explicit
- ambiguous cases handled explicitly
- tests needed for implementation are identified

## Implementation Notes / What Was Done

Not started.

## Open Follow-Ups

- default decision captured for implementation:
  - weak or unclear evidence does not create a fifth canonical trajectory state
  - no trajectory state is emitted when evidence is insufficient or non-directional
  - user-facing consumers may optionally render lightweight fallback language when it adds explanatory value
  - fading signal may later inform narrative-lifecycle reasoning, but Milestone 04 does not encode `story ended` as a trajectory state
