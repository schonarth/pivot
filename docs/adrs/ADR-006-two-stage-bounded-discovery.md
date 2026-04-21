---
name: Two-Stage Bounded Discovery
description: Deterministic pre-filter then capped shortlist; no LLM in scheduled discovery runs
type: reference
---

# ADR-006: Two-Stage Bounded Discovery

Status: Accepted
Date: 2026-04-19
SPEC: [SPEC-006-opportunity-discovery-pipeline](../specs/SPEC-006-opportunity-discovery-pipeline.md)

## Context

The system monitors held and watched assets but cannot surface new assets worth watching. A full-market LLM scan on every scheduled run would be unaffordably expensive and produce noisy, unauditable results.

## Decision

Use two stages: (1) deterministic technical pre-filter narrowing the eligible universe to ≤20 candidates, (2) context-aware deterministic ranking capped at 5 final survivors. Scheduled discovery runs are non-LLM. LLM refinement is available only on explicit user action. Watch handoff requires explicit user approval.

## Consequences

- Scheduled discovery cost is bounded and predictable
- LLM quality improvements are opt-in, not mandatory for every run
- Hard caps prevent brittleness from large survivor sets
- Watch scope mutation is always user-authorized; no silent additions
