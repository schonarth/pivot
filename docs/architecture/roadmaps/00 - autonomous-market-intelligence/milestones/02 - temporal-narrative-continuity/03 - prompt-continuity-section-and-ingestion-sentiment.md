# 03 - Prompt Continuity Section and Ingestion Sentiment

## Purpose

Define the compact continuity prompt addition and the ingestion-time sentiment path so Milestone 02 can explain narrative change without bloating prompts or prematurely implementing sentiment trajectory logic.

## Roadmap Milestone

Milestone 02 - Temporal Narrative Continuity

## Governing ADR

ADR-002 Narrative Continuity for Asset Context

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
- 02 - retention-labeling-and-persistence-shape.md

## Required Prior References

- `docs/architecture/adrs/ADR-002-narrative-continuity-for-asset-context.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/01 - asset-context-expansion/03 - deduplication-ranking-and-context-pack-shape.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/01 - asset-context-expansion/04 - implementation-validation-and-release-readiness.md`

## Likely Files Touched

- backend/ai/*
- backend/markets/*
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/02 - temporal-narrative-continuity/03 - prompt-continuity-section-and-ingestion-sentiment.md

## Entry Conditions

- retention and labeling rules finalized
- current Milestone 01 prompt shape reviewed
- ADR-002 ingestion-time sentiment direction reviewed

## Background

Milestone 02 only helps users if continuity reaches the prompt in a small, useful shape. ADR-002 also recommends ingestion-time sentiment as a companion signal, but only in its bounded Milestone 02 role. This task exists to keep both additions small, deterministic, and clearly separated from later trajectory work.

## Detailed Requirements

- define the exact prompt addition for the `story_so_far` continuity section
- keep the section compact:
  - at most `3-5` bullets or items
  - strongest recent continuity signals only
- define what information each prompt continuity item may include
- define the ingestion-time sentiment capture path:
  - labels `positive`, `neutral`, `negative`
  - attached to the persisted headline artifact
  - batch classification allowed when cheaper or faster
- explicitly exclude:
  - sentiment aggregation across days
  - improving / deteriorating / conflicting / reversal states
  - trajectory-driven recommendations

## Proposed Approach

- adapt the existing Milestone 01 prompt builder rather than creating a second prompt system
- keep prompt continuity input as a compact structured section derived from deterministic labels
- if ingestion sentiment is implemented, classify at fetch/ingest time or in a tightly adjacent path instead of backfilling old data
- keep stored sentiment optional for old rows and forward-only for new rows

## Validation Scenarios

- the model can answer “what changed?” from the prompt without being flooded with old headlines
- the prompt section remains compact when there is little continuity signal
- ingestion sentiment can support `shifted` detection without implying Milestone 04 trajectory logic
- lack of historical backfill does not block Milestone 02 rollout

## Task Steps

1. Define the compact `story_so_far` prompt section shape.
2. Define which continuity fields are exposed to the prompt and which remain internal.
3. Define the ingestion-time sentiment capture path and batching rules.
4. Confirm the design stays within ADR-002 scope and does not pull in Milestone 04.
5. Document prompt-budget risks and guardrails.

## Tests to Add or Update

- prompt-assembly tests for continuity-section inclusion
- tests for prompt compactness when continuity signal is absent or thin
- tests for ingestion sentiment attachment if implemented

## Commands to Run

- backend lint
- affected backend tests around prompt assembly and sentiment capture

## Exit Conditions

- continuity prompt section explicit
- ingestion sentiment path explicit
- prompt-budget guardrails explicit
- no Milestone 04 scope leak

## Implementation Notes / What Was Done

Added a compact `Story so far` section to the asset-insight prompt and wired forward-only ingestion-time sentiment scoring onto newly stored `NewsItem` rows.

## Open Follow-Ups

- none
