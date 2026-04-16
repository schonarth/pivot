# 03 - Deduplication, Ranking, and Context Pack Shape

## Purpose

Define the compact context pack shape and the deterministic rules that decide which headlines survive into the final asset analysis input.

## Roadmap Milestone

Milestone 01 - Asset Context Expansion

## Governing ADR

ADR-001 Open News Context Expansion

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
- 02 - source-selection-tagging-and-config-shape.md

## Required Prior References

- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces/01 - boundary-decision-and-current-state-scan.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces/02 - shared-vocabulary-and-interface-contracts.md`

## Likely Files Touched

- backend/*
- docs/architecture/adrs/ADR-001-open-news-context-expansion.md
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/01 - asset-context-expansion/03 - deduplication-ranking-and-context-pack-shape.md

## Entry Conditions

- source buckets defined
- tag set defined
- required Milestone 00 references reviewed

## Background

The value of Milestone 01 depends less on “fetching more headlines” and more on selecting a small, high-signal set that can fit inside a bounded prompt. This task translates ADR-001’s curation requirement into explicit rules for deduplication, ranking, and final context-pack shape.

## Detailed Requirements

- define exact duplicate handling
- define near-duplicate handling
- define ranking criteria in deterministic order
- define per-bucket limits if used
- define total prompt budget for the final asset context pack
- define the final shape consumed by asset analysis
- keep the pack compact, auditable, and free of reasoning fields
- do not add narrative memory, sentiment trajectory, or scenario fields in this milestone

## Proposed Approach

- express ranking in a stable order so equal inputs produce equal output ordering
- keep ranking factors simple and explainable:
  - recency
  - source quality
  - directness of match
  - likely impact
- prefer a context-pack shape that is easy to test and inspect in logs or fixtures
- if the current analysis consumer expects a different shape, define the smallest adapter needed rather than expanding the payload unnecessarily

## Validation Scenarios

- exact duplicate headlines from different fetches should collapse cleanly
- near-duplicate headlines about the same event should select the better representative item
- a symbol mention should not always outrank a higher-impact macro item if the macro item is the more relevant driver under the chosen rules
- context-pack output should stay within the prompt budget while preserving at least one high-value example from the relevant buckets

## Task Steps

1. Reuse the Milestone 00 context-pack and analysis-input boundary as the contract ceiling for this task.
2. Define exact duplicate and near-duplicate handling.
3. Define deterministic ranking factors such as:
   - recency
   - source quality
   - directness of match
   - likely market impact
4. Define per-bucket and total prompt budget limits.
5. Define the final context pack structure consumed by asset analysis without introducing reasoning fields.
6. Keep the output compact and auditable.
7. Avoid introducing recommendation or execution fields.

## Tests to Add or Update

- unit tests for deduplication behavior
- unit tests for deterministic ranking order
- smoke tests for prompt budget enforcement

## Commands to Run

- backend lint
- affected backend tests for ranking, deduplication, and context assembly
- frontend typecheck if output shape is consumed by client code

## Exit Conditions

- deterministic deduplication rules are explicit
- ranking order is testable
- prompt budget is explicit
- final context pack shape is stable enough for Milestone 01 integration

## Implementation Notes / What Was Done

Defined the compact context pack shape and deterministic selection rules.

What was done:

- specified duplicate handling through normalized headline signatures
- defined ranking order around directness, impact, source quality, and recency
- bounded the final pack with bucket caps and a total item cap
- kept the retained items compact and free of reasoning or execution fields

Open follow-ups:

- revisit whether source-quality ordering should stay hardcoded or move to a config artifact later

## Open Follow-Ups

- decide whether source quality should be static configuration or hardcoded ranking
