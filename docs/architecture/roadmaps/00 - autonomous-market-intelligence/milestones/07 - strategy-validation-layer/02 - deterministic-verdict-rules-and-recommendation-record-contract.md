# 02 - Deterministic Verdict Rules and Recommendation Record Contract

## Purpose

Define the canonical Milestone 07 validation contract so verdicting stays small, auditable, deterministic at the rule boundary, and reusable by later milestones without granting execution authority.

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
- `01 - candidate-intake-and-analysis-reuse-scan.md`

## Likely Files Touched

- backend/ai/*
- backend/models/*
- backend/tests/*
- docs/reference/*

## Entry Conditions

- candidate intake and reuse scan complete

## Background

Milestone 07 cannot stay honest if verdict semantics drift or if recommendation records are loosely shaped prose blobs. This task locks the structured verdict fields, minimum evidence payload, persistence contract, and deterministic fixture expectations.

## Detailed Requirements

- keep verdict vocabulary to:
  - `approve`
  - `reject`
  - `defer`
- define the hard-failure and insufficient-evidence paths that map to each verdict
- define the minimum stored record fields:
  - candidate identity
  - asset identity
  - technical inputs
  - context inputs
  - sentiment trajectory inputs
  - verdict
  - rationale
  - recorded timestamp
- keep prose subordinate to structured fields
- define deterministic fixtures for at least one approve, reject, and defer outcome

## Proposed Approach

1. Normalize the candidate input into a compact internal contract.
2. Build a bounded evidence pack from existing artifacts.
3. Evaluate the pack against explicit milestone rules.
4. Persist the canonical recommendation record.
5. Layer display text on top without making it the system of record.

## Validation Scenarios

- clear approve: technical setup and context support align
- clear reject: one or more hard requirements fail
- honest defer: evidence is incomplete or materially conflicted

## Task Steps

1. Review the requirement and expected behavior.
2. Define or confirm the canonical record shape.
3. Implement the smallest correct verdicting rules.
4. Add fixture-driven regression tests.
5. Run verification commands.

## Tests to Add or Update

- fixture-based verdict tests for approve, reject, defer
- persistence tests for canonical recommendation record fields
- regression tests for missing or conflicting evidence handling

## Commands to Run

- `cd backend && ruff check .`
- `cd backend && pytest`

## Exit Conditions

- verdict semantics are explicit
- recommendation record contract is canonical
- fixtures cover core milestone outcomes
- structured fields remain the source of truth

## Implementation Notes / What Was Done

Short note describing what was actually implemented, especially if it differs from the plan.

## Open Follow-Ups

- none
