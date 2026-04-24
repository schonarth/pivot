# 01 - Candidate Intake and Analysis Reuse Scan

## Purpose

Identify the smallest correct insertion points for strategy validation so Milestone 07 can accept explicit paper-trade candidates and reuse existing analysis artifacts without creating a second market-understanding pipeline.

## Roadmap Milestone

Milestone 07 - Strategy Validation Layer

## Governing SPEC

SPEC-007 Strategy Validation with Technical and Context Inputs

## Status

planned

## Owner

unassigned

## Date Started

YYYY-MM-DD

## Date Completed

YYYY-MM-DD

## Branch

feat/autonomous/07-strategy-validation

## Dependencies

- `00 - milestone coordination.md`

## Likely Files Touched

- backend/ai/*
- backend/mcp/*
- backend/portfolios/*
- backend/tests/*
- frontend/src/views/*
- frontend/src/components/*
- docs/reference/*

## Entry Conditions

- SPEC-007 approved
- milestone coordination reviewed

## Background

Milestone 07 is only bounded if candidate intake is explicit and the validation layer reuses the current technical, context, trajectory, and divergence outputs where available. This task defines where those inputs already exist, where they can be fetched honestly, and where manual-trade initiation should attach without becoming a hidden execution dependency.

## Detailed Requirements

- identify the current sources of:
  - explicit trade candidate data
  - technical evidence
  - context summary inputs
  - sentiment trajectory inputs
  - divergence inputs if available and relevant
- identify the smallest backend insertion point for paper-only validation requests
- identify the smallest frontend or MCP consumer surface for an opt-in `Should I?` request
- confirm that manual trade submit stays separate from validation request plumbing
- document any missing artifact that must be added before deterministic verdicting can be honest

## Task Steps

1. Review the requirement and expected behavior.
2. Scan the existing manual trade flow, asset analysis pipeline, and monitored-set consumers.
3. Map which analysis artifacts can be reused directly and which need bounded adapters.
4. Choose the candidate request shape for Milestone 07.
5. Document the chosen insertion points and any explicit gaps.
6. Add or update tests if code changes are required for the scan outcome.
7. Run verification commands.

## Tests to Add or Update

- none expected unless scan findings require code changes

## Commands to Run

- `cd backend && pytest -q`
- `cd frontend && npm run typecheck`

## Exit Conditions

- candidate intake path is explicit
- reuse points for existing analysis artifacts are documented
- validation and execution boundaries are separate
- any blocker is concrete and named

## Implementation Notes / What Was Done

Short note describing what was actually implemented, especially if it differs from the plan.

## Open Follow-Ups

- none
