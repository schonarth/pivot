---
name: Bounded Strategy Validation
description: Deterministic verdict layer for paper-only trade validation; execution boundary stays closed
type: reference
---

# ADR-007: Bounded Strategy Validation With Closed Execution Boundary

Status: Draft
Date: 2026-04-21
SPEC: [SPEC-007-strategy-validation-with-technical-and-context-inputs](../specs/SPEC-007-strategy-validation-with-technical-and-context-inputs.md)

## Context

The system can analyze markets and surface opportunities but cannot validate a proposed trade idea in a disciplined, auditable way before execution. Without a bounded validation layer, analysis cannot be turned into a reviewable paper-only decision workflow.

## Decision

Add a deterministic strategy-validation layer that accepts an explicit candidate, evaluates it against existing technical, context, and trajectory inputs, and emits one of three verdicts (`approve`, `reject`, `defer`). Every verdict is persisted as a paper-only recommendation record. The execution boundary stays closed — no orders are placed.

## Consequences

- Trade validation is auditable: inputs, verdict, and rationale are all stored
- Three-verdict vocabulary forces honest `defer` outcomes rather than false binary decisions
- Validation reuses existing analysis artifacts; no parallel context store is introduced
- Autonomous execution gating in future milestones can build on the same verdict contract
