# 01 - Continuity Insertion Point and Retained Artifact Scan

## Purpose

Find the smallest correct insertion point for temporal continuity and identify what artifact should be retained across days before adding new persistence or prompt behavior.

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
- Milestone 01 implementation complete enough to provide a current asset context pack

## Required Prior References

- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces/01 - boundary-decision-and-current-state-scan.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces/02 - shared-vocabulary-and-interface-contracts.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces/03 - current-consumers-and-storage-touchpoints.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/01 - asset-context-expansion/01 - existing-pipeline-scan-and-insertion-point.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/01 - asset-context-expansion/04 - implementation-validation-and-release-readiness.md`

## Likely Files Touched

- backend/ai/*
- backend/markets/*
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/02 - temporal-narrative-continuity/01 - continuity-insertion-point-and-retained-artifact-scan.md

## Entry Conditions

- SPEC-002 reviewed
- milestone coordination reviewed
- required Milestone 00 and Milestone 01 references reviewed

## Background

SPEC-002 requires continuity to stay an extension of context building, not a second reasoning system. Before implementation, Milestone 02 must identify where the current context pack is assembled, what compact artifact should be retained, and whether the existing `NewsItem` path already provides enough temporal fields.

## Detailed Requirements

- identify the current code path that assembles the Milestone 01 asset context pack
- identify the narrowest insertion point for continuity retrieval and labeling
- determine whether the continuity unit should be:
  - retained selected context items
  - retained `NewsItem` rows plus Milestone 01 recomputation
  - another compact artifact justified by SPEC-002
- identify which current persisted fields already satisfy continuity needs
- identify any storage or coupling risks that would make continuity implementation unsafe
- do not design the full persistence solution in this task

## Proposed Approach

- start from the current asset-analysis consumer and trace backward through Milestone 01 context assembly
- compare SPEC-002 retention requirements against existing persisted data
- prefer reusing existing artifacts or a small additive record over replaying full prompts
- document the insertion point and the retention candidate in terms of files, functions, and boundaries

## Validation Scenarios

- after reading this file, an implementation agent should know where continuity belongs
- the file should say whether continuity can reuse existing `NewsItem` rows or needs an additive artifact
- any storage expansion should remain clearly smaller than a narrative-history system
- any coupling risk between continuity and reasoning should be called out explicitly

## Task Steps

1. Trace the current Milestone 01 asset-analysis path and context-pack assembly.
2. Identify the continuity insertion point that preserves the Milestone 00 context/reasoning/execution boundary.
3. Compare SPEC-002 required fields against current persisted news and context artifacts.
4. Recommend the smallest retained artifact that supports short-memory continuity.
5. Document any coupling, storage, or prompt-budget risks that later tasks must respect.

## Tests to Add or Update

- add or update smoke coverage around the identified insertion point once implementation starts
- preserve current asset-analysis behavior while continuity is absent or thin

## Commands to Run

- backend lint
- affected backend tests around asset analysis and news retrieval

## Exit Conditions

- insertion point identified
- retained continuity unit identified or narrowed to one small choice
- existing reusable fields and helpers documented
- storage-expansion risks documented

## Implementation Notes / What Was Done

The continuity insertion point is the existing `AIService.analyze_asset` flow, with `build_asset_context_pack()` as the narrow handoff into prompt assembly.

The retained continuity unit is the persisted `NewsItem` row, reused through a short bounded lookback window instead of a new narrative table.

## Open Follow-Ups

- none
