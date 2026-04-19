# 02 - Deterministic Prefilter and Ranking Rules

## Purpose

Turn ADR-006's approved discovery decisions into an exact deterministic contract for eligibility, survivor caps, and shortlist ordering before any implementation slice begins.

## Roadmap Milestone

Milestone 06 - Opportunity Discovery

## Governing ADR

ADR-006 Opportunity Discovery Pipeline

## Status

planned

## Owner

unassigned

## Branch

feat/autonomous/06-opportunity-discovery

## Dependencies

- 00 - milestone coordination.md
- 01 - discovery-universe-and-insertion-point-scan.md

## Required Prior References

- `docs/architecture/adrs/ADR-004-sentiment-trajectory-and-narrative-state.md`
- `docs/architecture/adrs/ADR-005-divergence-reasoning-for-market-analysis.md`
- `docs/architecture/adrs/ADR-006-opportunity-discovery-pipeline.md`

## Likely Files Touched

- backend/ai/*
- backend/markets/*
- backend/tests/*
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/06 - opportunity-discovery/02 - deterministic-prefilter-and-ranking-rules.md

## Entry Conditions

- universe and insertion-point scan documented
- approved ADR-006 decisions reviewed

## Background

Milestone 06 now fixes the broad product choices: one market-scoped stored asset universe, a small assertive pre-filter, `20 -> 5` caps, and a small blended deterministic ranking score. This task translates those decisions into exact implementation rules, thresholds, and data-shape expectations.

## Detailed Requirements

- define the exact liquidity floor rule
- define the exact trend-intact rule
- define the exact breakout or near-breakout confirmation rule
- define survivor cap behavior and tie handling for the `20` pre-filter outputs
- define the small blended deterministic score used to order survivors into the final `5`
- define ranking inputs for:
  - technical setup quality
  - breakout proximity or confirmation quality
  - bounded context support
  - freshness
- keep the scoring logic small, documented, and auditable
- avoid LLM dependence or wide scoring sprawl

## Proposed Approach

- translate the approved pre-filter recipe into a small number of exact thresholds
- document deterministic tie-break rules so shortlist behavior is stable
- prefer interpretable dimensions over many overlapping sub-weights
- ensure context support and freshness stay bounded and can be computed without hidden model calls

## Validation Scenarios

- a candidate with insufficient liquidity never reaches the survivor set
- a candidate with liquidity but no intact trend fails the pre-filter
- a candidate with intact trend but no breakout or near-breakout signal fails the pre-filter
- more than `20` eligible survivors are reduced deterministically
- the final ranking can explain why one candidate outranks another using stored inputs only

## Task Steps

1. Define the exact deterministic pre-filter thresholds.
2. Define survivor-cap and tie-break behavior.
3. Define the small blended ranking dimensions and their score combination.
4. Define the deterministic inputs for bounded context support and freshness.
5. Identify the tests needed to lock the rules before implementation.

## Tests to Add or Update

- pre-filter eligibility tests for pass and fail cases
- survivor-cap and tie-break regression tests
- ranking-order tests for representative candidate sets
- tests proving context support and freshness do not require LLM calls

## Commands to Run

- `cd backend && ruff check .`
- run affected backend tests around discovery filters and ranking helpers

## Exit Conditions

- pre-filter thresholds explicit
- survivor-cap behavior explicit
- ranking dimensions explicit
- tie-break behavior explicit
- required regression tests identified

## Implementation Notes / What Was Done

To be filled during execution.

## Open Follow-Ups

- none
