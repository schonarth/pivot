# 01 - Boundary Decision and Current-State Scan

## Purpose

Document the current system boundaries and define where context selection should stop and reasoning or execution should begin.

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

## Likely Files Touched

- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces/01 - boundary-decision-and-current-state-scan.md
- backend/*
- frontend/*
- docs/reference/prd-mlp.md
- docs/reference/prd-paper-trader.md

## Entry Conditions

- milestone coordination file reviewed
- roadmap reviewed

## Background

Milestone 00 exists to reduce ambiguity before user-facing intelligence work begins. The first baseline need is to understand the system as it already exists and to define where future context-selection work should stop. Without that decision, Milestone 01 risks mixing news gathering, analysis composition, and trading logic in one path.

This task creates the architectural baseline that later milestone tasks can reference instead of repeatedly rediscovering the same seams.

## Detailed Requirements

- identify the current locations of:
  - news ingestion or retrieval
  - technical analysis generation
  - prompt or context assembly
  - analysis generation
  - trade or alert execution
- describe the current flow in concrete system terms, not abstract product language
- define a future-facing separation rule:
  - context selection prepares candidate inputs
  - reasoning interprets those inputs
  - execution acts only on approved outputs
- identify any existing code paths where these responsibilities are currently mixed
- do not propose large refactors in this task
- do not change behavior unless a small protective documentation or interface clarification edit is necessary

## Proposed Approach

- start with a quick repo scan of backend services, MCP- or AI-related code paths, prompt-building utilities, and any current asset analysis flows
- map the flow in the smallest useful form: entrypoint, helpers, outputs, side effects
- capture only the coupling points that matter for later milestones
- if the current code already has useful abstractions, name them explicitly so later tasks reuse them instead of creating parallel paths

## Validation Scenarios

- if a current asset analysis path exists, the scan should be able to point to the exact place where symbol-only context is assembled today
- if news retrieval and prompt assembly already live in different layers, the document should preserve that separation rather than collapsing them conceptually
- if one code path both interprets data and decides actions, that should be named as a coupling risk for later milestones
- a later Milestone 01 task should be able to read this file and identify where context-expansion work belongs without rescanning the entire repo

## Task Steps

1. Scan the project for current news ingestion, technical analysis, prompt building, analysis generation, and trade execution behavior.
2. Identify current seams between data collection, prompt/context assembly, reasoning, and user-visible outputs.
3. Document the current-state architecture in concise form.
4. Define the intended Milestone 00 boundary rule:
   - context selection prepares inputs
   - reasoning interprets inputs
   - execution acts on approved outputs
5. Call out any current coupling that later milestones must avoid reinforcing.
6. Keep recommendations minimal and architectural.

## Tests to Add or Update

- docs-only baseline task
- no direct unit tests expected unless code is touched to expose or preserve interfaces

## Commands to Run

- if code is touched: run relevant lint, typecheck, and affected tests

## Exit Conditions

- current-state boundary map exists
- intended future separation between context, reasoning, and execution is explicitly documented
- risky existing coupling points are listed
- later milestone tasks can reference this file without re-scanning the full codebase from scratch

## Implementation Notes / What Was Done

Not started.

## Open Follow-Ups

- decide whether any existing code needs protective refactoring before Milestone 01
