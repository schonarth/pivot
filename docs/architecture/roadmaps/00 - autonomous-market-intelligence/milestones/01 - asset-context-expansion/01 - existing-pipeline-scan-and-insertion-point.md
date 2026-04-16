# 01 - Existing Pipeline Scan and Insertion Point

## Purpose

Find the smallest correct insertion point for asset context expansion by scanning the current news and asset analysis pipeline before changing behavior.

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
- Milestone 00 core baseline outputs complete enough to unblock Milestone 01

## Required Prior References

- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces/01 - boundary-decision-and-current-state-scan.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces/02 - shared-vocabulary-and-interface-contracts.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces/03 - current-consumers-and-storage-touchpoints.md`

## Likely Files Touched

- backend/*
- frontend/*
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/01 - asset-context-expansion/01 - existing-pipeline-scan-and-insertion-point.md

## Entry Conditions

- ADR-001 reviewed
- milestone coordination reviewed
- required Milestone 00 references reviewed

## Background

ADR-001 defines what Milestone 01 should do, but not yet where the change belongs in the existing implementation. This task prevents “parallel architecture” by forcing the milestone to find the real insertion point first. The goal is to reuse the current asset-analysis pipeline and add a compact context-building step at the smallest responsible point.

## Detailed Requirements

- identify the current path that produces asset analysis and any current news-aware prompt assembly
- identify where symbol-only context is selected today, if it exists
- find the smallest insertion point where broader context can be added without:
  - moving reasoning logic into retrieval
  - moving execution logic into context assembly
  - duplicating the current analysis flow
- identify reusable abstractions, helpers, services, serializers, or prompt builders
- identify any code smells or coupling risks that would make the insertion unsafe
- do not redesign the whole analysis stack in this task

## Proposed Approach

- start from the current user-facing consumer and trace backward to the data assembly path
- prefer adapting an existing backend path over inventing a second analysis or context service unless the scan proves none exists
- document the insertion point in terms of files, functions, and boundaries
- if frontend code only renders already-produced analysis, keep Milestone 01 logic on the producer side unless evidence shows otherwise

## Validation Scenarios

- after reading this file, an implementation agent should know exactly where to add context-expansion logic
- if current code already has a helper suitable for context assembly, this file should name it
- if current code mixes prompt building and execution concerns, that should be flagged as risk instead of silently preserved
- if no clear symbol-only insertion point exists, the file should say so and recommend the narrowest new abstraction needed

## Task Steps

1. Read the required Milestone 00 references before rescanning code.
2. Scan the current backend and frontend paths that produce asset analysis and news-aware prompts.
3. Identify where symbol-only context is selected today.
4. Identify the minimal insertion point for a new context-building step that preserves the Milestone 00 context/reasoning/execution boundary.
5. Record any existing abstractions that should be reused rather than replaced.
6. Call out any risky coupling that would cause context selection to bleed into reasoning or execution.

## Tests to Add or Update

- add or update smoke coverage around the insertion point once implementation starts
- preserve current asset analysis happy path behavior while broadening context inputs

## Commands to Run

- backend lint
- frontend typecheck if frontend files are touched
- affected tests around asset analysis and news retrieval

## Exit Conditions

- minimal integration point is identified
- existing reusable code paths are listed
- duplication risks are documented
- later implementation tasks can proceed without rediscovering the pipeline

## Implementation Notes / What Was Done

Completed the pipeline scan and identified the insertion point.

What was done:

- traced the current per-asset analysis path from frontend and MCP consumers into `AIService.analyze_asset`
- confirmed the existing news-aware prompt assembly lives in `backend/ai/services.py`
- identified the smallest safe insertion point as a backend context-pack builder inside the shared AI service
- verified the frontend only consumes the already-produced analysis output, so Milestone 01 stays on the producer side

Open risks noted:

- symbol-only news selection existed in the shared AI service
- prompt-building and context selection were coupled in one backend path, so the later implementation task had to add a narrow adapter rather than a second analysis flow

## Open Follow-Ups

- confirm whether context assembly belongs wholly in backend or is partially split today
