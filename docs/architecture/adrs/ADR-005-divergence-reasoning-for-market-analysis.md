---
name: Divergence Reasoning for Market Analysis
description: Draft ADR for comparing expected and actual market behavior with bounded, auditable explanations
type: reference
---

# ADR

## ADR-005 Divergence Reasoning for Market Analysis

Status: Draft

## Roadmap Position

This ADR corresponds to Milestone 5 of the Autonomous Market Intelligence roadmap:

- [Autonomous Market Intelligence Roadmap](../roadmaps/00%20-%20autonomous-market-intelligence/roadmap.md)

Its role is narrow: explain why an asset or monitored set moved differently from what the current technical and context inputs suggested.

It is not intended to authorize trading, replace trajectory analysis, or build a long-horizon market prediction engine.

## Context

ADR-001 broadens context selection. ADR-002 adds bounded continuity for one asset. ADR-003 expands that context to portfolio and watch scopes. ADR-004 adds short-window sentiment trajectory.

That still leaves a gap: the system can describe context, continuity, and sentiment direction, but it cannot yet explain why price action matched or contradicted those inputs.

Users eventually need answers such as:

- why did a positive headline not move the price
- why did a negative news flow not break the trend
- why did price reverse while the narrative was still constructive
- why did a monitored set behave differently from the asset-level tone

Without a bounded divergence layer, the system can summarize what happened, but it cannot clearly explain expected-vs-actual behavior across the same short window.

## Decision

Milestone 5 should add a deterministic short-window divergence-reasoning layer on top of the shared analysis inputs.

That layer should:

1. derive an expected direction from the current technical and context inputs
2. compare that expectation to the recent actual price move
3. classify the mismatch, if any, into a small auditable set of divergence labels
4. expose the result as analysis input only, not as execution logic

The divergence layer should stay small, auditable, and bounded to the same short retention window used by the analysis pipeline. It should not become a durable market-timing system or a trade-decision system.

The first consumers should be:

1. asset analysis
2. monitored-set analysis where the same shared inputs exist

Implementation priority:

- use the shared context, continuity, and trajectory signals first
- derive divergence deterministically before any explanatory prose
- reuse the same contract for asset and monitored-set consumers whenever the inputs are available
- do not create a separate long-horizon reasoning stack for divergence

## Intended Shape

The future implementation should treat divergence reasoning as an enrichment of the existing analysis output, not as a replacement for the analysis pipeline.

Expected flow:

1. build the current analysis inputs
2. derive the expected direction from technical and context signals
3. read the recent actual price move for the same short window
4. classify the relationship between expectation and actual move
5. emit a compact divergence summary for downstream reasoning

The divergence summary should remain compact and bounded. It should not require storing free-form narrative prose as the system of record.

## Resolved Decisions

### Expected Direction

Milestone 5 should derive expected direction from the existing analysis inputs rather than asking the LLM to invent the comparison.

Meaning:

- technical posture remains one input
- news context remains one input
- sentiment trajectory may be used as a supporting input when available
- the final divergence label remains deterministic

### Actual Move

Milestone 5 should compare expectation against the recent actual move over the same bounded window.

Meaning:

- the comparison should use recent market price change or an equivalent short-window move signal
- the divergence layer should not depend on unbounded historical replay
- the comparison should remain auditable from stored inputs

### Divergence Labels

Milestone 5 should support at least the following labels:

- `priced_in`
- `ignored_signal`
- `competing_macro_priority`
- `reversal`
- `uncertainty_conflict`

Meaning:

- `priced_in`: the expected move was already reflected in price
- `ignored_signal`: the expected move did not materialize and the market stayed flat or moved the other way for reasons not dominated by a stronger competing signal
- `competing_macro_priority`: a broader market force outweighed the asset-specific signal
- `reversal`: the market moved in the opposite direction from the near-term expectation
- `uncertainty_conflict`: the inputs were too mixed or weak to produce a cleaner explanation

### Prompt and Output Shape

Milestone 5 should add one compact divergence section to downstream reasoning input.

Expected shape:

- `divergence_analysis`
- compact expected-vs-actual comparison
- enough detail to explain the mismatch without turning the prompt into a timeline dump

The divergence section should help the model explain why the market ignored, priced in, or overrode the apparent signal.

### Persistence Boundary

Milestone 5 should compute divergence on read from existing analysis inputs and recent market data.

Allowed persistence for this milestone:

- the existing short-window inputs that already feed analysis
- compact sentiment trajectory data from Milestone 04 when available

Allowed optimization:

- thin ephemeral non-canonical caching only when it remains a pure optimization layer and can be dropped without affecting correctness or auditability

Not approved in this milestone:

- long-horizon divergence history as a new canonical store
- persisted derived divergence artifacts as a new canonical record
- trade execution signals derived directly from divergence
- model-generated prose as the canonical divergence record

### Execution Boundary

Milestone 5 should expose divergence as analysis input only.

Not approved in this milestone:

- direct trade approval from divergence alone
- autonomous trade triggers from divergence labels
- strategy execution side effects

Those belong to later milestones.

## Constraints

- Keep divergence bounded to the same short explicit window.
- Keep the explanation auditable from existing analysis inputs.
- Prefer deterministic classification before reasoning.
- Reuse existing context, continuity, and trajectory artifacts where possible.
- Keep analysis enrichment separate from execution.

## Non-Goals

- Direct trade execution from divergence alone
- Long-horizon market forecasting
- Complex ML training loops
- Full portfolio strategy logic
- Unbounded narrative history

## Notes

This ADR should remain independently mergeable and user-releaseable when implemented.

Expected user-facing value:

- analysis can explain why the market moved differently from the apparent news or technical setup instead of only restating the inputs
