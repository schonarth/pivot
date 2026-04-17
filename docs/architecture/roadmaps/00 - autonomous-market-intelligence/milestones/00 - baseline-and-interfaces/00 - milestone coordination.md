# 00 - Milestone Coordination

## Purpose

Coordinate Milestone 00 execution so the project establishes clean boundaries for context selection, analysis, and execution before user-facing intelligence work begins.

## Roadmap Milestone

Milestone 00 - Baseline and Interfaces

## Governing ADR

Roadmap-only planning task. Milestone 00 exists to prepare the baseline boundary document and shared interfaces before later roadmap ADRs depend on them.

## Status

done

## Owner

GPT-5.4 / coordination

## Branch

feat/autonomous/00-baseline

## Date Started

2026-04-15

## Date Completed

2026-04-15

## Dependencies

- none

## Likely Files Touched

- docs/architecture/roadmaps/00 - autonomous-market-intelligence/roadmap.md
- docs/architecture/execution/milestone-delivery-execution-model.md
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces/*
- backend/*
- frontend/*

## Entry Conditions

- roadmap approved
- milestone folder exists
- no later milestone work has started that would depend on undocumented baseline interfaces

## Task Steps

1. Read the roadmap and execution model in full.
2. Quickly scan the current backend and frontend for existing analysis, news, technical signal, prompt, and execution boundaries.
3. Complete the milestone task specs in order.
4. Keep scope strictly to baseline interfaces and vocabulary.
5. Do not introduce user-facing behavior changes in this milestone.
6. Prepare milestone-end summary, smoke verification, and integration verification notes for UAT.

## Tests to Add or Update

- docs-only coordination task
- no direct unit tests expected in this file
- later milestone tasks must define any code-level tests they require

## Commands to Run

- none expected for this coordination task unless code changes are introduced while executing later milestone tasks

## Exit Conditions

- Milestone 00 task files are complete and internally consistent.
- Boundary definitions exist for context selection, analysis, and execution.
- Shared vocabulary exists for asset, portfolio, watch, and strategy scopes.
- Current consumers and likely storage touchpoints are documented.
- Milestone can hand off cleanly to Milestone 01.

## Implementation Notes / What Was Done

Completed Milestone 00 as a docs-only baseline pass.

What was done:

- read the roadmap and milestone delivery execution model in full before changing milestone specs
- scanned current backend and frontend entrypoints for news retrieval, technical analysis, prompt assembly, AI analysis, and execution paths
- completed the milestone task specs in order:
  - `01 - boundary-decision-and-current-state-scan.md`
  - `02 - shared-vocabulary-and-interface-contracts.md`
  - `03 - current-consumers-and-storage-touchpoints.md`
- kept scope to boundary definitions, vocabulary, current consumers, and storage touchpoints
- documented current coupling risks without proposing milestone-00 refactors

Milestone-end summary:

- current asset-level analysis flow identified across first-party UI and MCP entrypoints
- separation rule documented: context selection prepares inputs, reasoning interprets inputs, execution acts only on approved outputs
- shared vocabulary defined for asset, portfolio, watch, and strategy scopes
- current and near-term consumers documented in roadmap dependency order
- transient versus persistent storage boundaries documented for news, technical signals, and analysis artifacts

Smoke verification notes for UAT handoff:

- docs remain internally consistent with the approved roadmap milestone definition
- no user-facing behavior changed
- no database schema, API contract, or runtime behavior changed in this milestone

Integration verification notes for UAT handoff:

- current frontend per-asset analysis consumer: `frontend/src/components/AssetAnalysisTab.vue`
- current authenticated backend entrypoint: `backend/markets/views.py` `AssetViewSet.ai_insight`
- current agent-facing backend entrypoint: `backend/mcp/views.py` `MCPAssetInsightView`
- current analysis service boundary and coupling hotspot: `backend/ai/services.py` `AIService.analyze_asset`
- current execution paths held separate from analysis output:
  - manual and agent trade execution in `backend/trading/views.py`
  - alert auto-trade in `backend/alerts/services.py`
  - strategy execution in `backend/strategies/tasks.py`

## Open Follow-Ups

- decide whether Milestone 00 should later be backed by a dedicated baseline ADR
