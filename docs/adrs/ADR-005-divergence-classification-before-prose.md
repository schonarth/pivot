---
name: Divergence Classification Before Prose
description: Deterministic expected-vs-actual classification before any LLM prose explanation
type: reference
---

# ADR-005: Deterministic Divergence Classification Before LLM Prose

Status: Accepted
Date: 2026-04-18
SPEC: [SPEC-005-divergence-reasoning-for-market-analysis](../specs/SPEC-005-divergence-reasoning-for-market-analysis.md)

## Context

The system can describe context, continuity, and sentiment direction but cannot explain why price action matched or contradicted those inputs. Letting the LLM invent both the classification and explanation in one step produces inconsistent, unauditable results.

## Decision

Derive expected direction from existing analysis inputs using a strict-consensus rule, classify actual price move via thresholded net percent change, and emit one of six canonical divergence labels before any prose is generated. The LLM explains an already-classified divergence; it does not classify it.

## Consequences

- Divergence labels are deterministic, reproducible, and testable with frozen fixtures
- Six labels cover most cases; novel market behaviors may not map cleanly
- Expected direction derivation depends on technical and context inputs being available and consistent
- Structured output is the canonical record; prose is optional and decorative
