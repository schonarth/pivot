---
name: Shared Pipeline for Monitored Sets
description: One shared context pipeline for asset, portfolio, and watch scopes instead of separate prompt paths
type: reference
---

# ADR-003: Shared Pipeline for Monitored Sets

Status: Accepted
Date: 2026-04-16
SPEC: [SPEC-003-context-scope-expansion-asset-portfolio-watchlist](../specs/SPEC-003-context-scope-expansion-asset-portfolio-watchlist.md)

## Context

Users think in monitored sets (portfolios, watchlists), not just individual assets. Building separate prompt paths for each scope would duplicate logic and fragment the shared vocabulary established in earlier milestones.

## Decision

Generalize the existing context pipeline to support asset, portfolio, and watch scopes through scoped views over the same monitored-asset set. Monitored-set membership stays explicit and deterministic — no auto-discovery or inference.

## Consequences

- Single context-building path serves all scopes; vocabulary stays consistent
- Shared macro/sector events are deduplicated via clustering before composition
- Watch and portfolio scope are bounded by explicit membership, not inferred sets
- Future milestones (sentiment trajectory, discovery) inherit the same scope boundary
