---
name: Bounded Continuity Layer
description: Short-memory continuity as a bounded enrichment layer, not a durable narrative engine
type: reference
---

# ADR-002: Bounded Continuity Layer, Not a Durable Narrative Engine

Status: Accepted
Date: 2026-04-16
SPEC: [SPEC-002-narrative-continuity-for-asset-context](../specs/SPEC-002-narrative-continuity-for-asset-context.md)

## Context

Without temporal memory, each asset analysis is an isolated snapshot. Users need to know what changed versus what is continuing, but a full narrative engine would add unbounded storage and reasoning complexity.

## Decision

Add a small, bounded continuity layer that retains a short window of prior context items and classifies each as `new`, `continuing`, or `shifted`. This layer enriches analysis input; it does not become a separate reasoning system or durable store.

## Consequences

- Analysis can distinguish fresh catalysts from ongoing narratives
- Memory window is explicitly bounded; no unbounded storage commitment
- Continuity artifacts are reusable by later milestones (sentiment trajectory, monitored sets)
- Long-horizon narrative tracking is explicitly deferred
