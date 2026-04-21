---
name: Deterministic Context Selection
description: Deterministic ranking and selection over LLM-driven retrieval for asset news context
type: reference
---

# ADR-001: Deterministic Context Selection Over LLM-Driven Retrieval

Status: Accepted
Date: 2026-04-13
SPEC: [SPEC-001-open-news-context-expansion](../specs/SPEC-001-open-news-context-expansion.md)

## Context

Asset context expansion requires selecting relevant headlines from multiple buckets (symbol, company, sector, macro, theme). The selection mechanism must be predictable and cost-controlled at high frequency.

## Decision

Use deterministic rules — bucket-specific caps, deduplication, and scoring heuristics — for all context selection and ranking. The LLM consumes the curated result; it does not decide the curation.

## Consequences

- Context selection is auditable and reproducible without model calls
- Recall flexibility is lower than a retrieval-augmented approach
- Cost and latency are predictable and bounded
- Future milestones may layer LLM refinement on top of deterministic shortlists, not replace them
