---
name: Deterministic Sentiment Trajectory
description: Fixed 4-state trajectory model scored deterministically before LLM explanation
type: reference
---

# ADR-004: Deterministic Sentiment Trajectory With Fixed 4-State Model

Status: Accepted
Date: 2026-04-18
SPEC: [SPEC-004-sentiment-trajectory-and-narrative-state](../specs/SPEC-004-sentiment-trajectory-and-narrative-state.md)

## Context

Analysis can retain and classify context items, but cannot yet explain the direction of sentiment across them. An open-ended LLM-invented state space would be unauditable and inconsistent across runs.

## Decision

Use exactly four trajectory states (`improving`, `deteriorating`, `conflicting`, `reversal`) scored by deterministic thresholding over per-item sentiment labels before any LLM explanation is generated. The LLM explains an already-classified state; it does not invent the state.

## Consequences

- Trajectory states are consistent and auditable without inspecting model reasoning
- Expressiveness is constrained to four states; edge cases may need `conflicting` as a catch-all
- Sentiment unit and base labels must be defined before trajectory scoring, creating an upstream dependency
- Trajectory layer feeds naturally into divergence reasoning (Milestone 5)
