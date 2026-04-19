---
name: Divergence Reasoning for Market Analysis
description: Draft ADR for comparing expected and actual market behavior with bounded, auditable explanations
type: reference
---

# ADR

## ADR-005 Divergence Reasoning for Market Analysis

Status: Approved

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

Milestone 5 should use a strict-consensus expectation rule for the first implementation.

Default direction policy:

- a directional expectation is emitted only when the relevant directional inputs agree
- mixed directional inputs do not collapse into a weighted directional vote for this milestone
- partial evidence without agreement does not create a directional expectation

Expected first-pass behavior:

- `positive` plus `positive` => expected `up`
- `negative` plus `negative` => expected `down`
- `positive` plus `negative` => `uncertainty_conflict`
- `positive` plus `neutral`, or `negative` plus `neutral`, or insufficient inputs => `insufficient_signal`

This milestone favors precision and auditability over maximum directional coverage. Thresholds or weighting can be tuned in later work if the system proves too quiet.

### Actual Move

Milestone 5 should compare expectation against the recent actual move over the same bounded window.

Meaning:

- the comparison should use recent market price change or an equivalent short-window move signal
- the divergence layer should not depend on unbounded historical replay
- the comparison should remain auditable from stored inputs

Milestone 5 should use thresholded net percent move for the first implementation.

Default move policy:

- compare the earliest in-window price against the latest in-window price
- derive actual move from net percent change over that bounded window
- classify tiny moves as `flat` rather than forcing `up` or `down`

Default threshold:

- use one global flat-move threshold constant for the milestone
- initial value: `0.5%`
- expected implementation shape: one easily tuned constant such as `DIVERGENCE_FLAT_MOVE_THRESHOLD = 0.005`

This milestone does not require market-specific or volatility-adjusted thresholds.

### Divergence Labels

Milestone 5 should support at least the following labels:

- `no_divergence`
- `insufficient_signal`
- `no_material_follow_through`
- `competing_macro_priority`
- `reversal`
- `uncertainty_conflict`

Meaning:

- `no_divergence`: a clear expectation existed and the actual move aligned with it inside the bounded window
- `insufficient_signal`: the available inputs did not provide enough directional evidence to form a clear expectation
- `no_material_follow_through`: the expected move did not materially appear inside the bounded window; the signal may already have been absorbed or may have been deprioritized by the market, but Milestone 5 does not force that distinction
- `competing_macro_priority`: a broader market force outweighed the asset-specific signal and that broader force is supported by explicit monitored-set or shared-context evidence inside the bounded window
- `reversal`: the market moved in the opposite direction from the near-term expectation
- `uncertainty_conflict`: the expectation-stage inputs materially pointed in opposing directions

Note:

- Milestone 5 intentionally merges the intuitively appealing `priced_in` and `ignored_signal` narratives into `no_material_follow_through`
- inside the same bounded short window, the system can often detect that the expected reaction did not materially appear, but it cannot reliably or auditably prove whether that happened because the signal was already absorbed or because the market chose not to respond
- forcing that distinction inside this milestone would create false precision and weaken the deterministic boundary of the divergence layer
- `uncertainty_conflict` is reserved for genuine directional disagreement between expectation-stage inputs; weak or partial evidence should use `insufficient_signal` instead
- `competing_macro_priority` should be rare; `reversal` remains the default contradiction label unless broader-force evidence is explicit and auditable

Expected classification boundary:

- clear expectation plus aligned actual move => `no_divergence`
- clear expectation plus flat actual move => `no_material_follow_through`
- clear expectation plus opposite actual move => `reversal`
- clear expectation plus opposite actual move and explicit broader-force confirmation => `competing_macro_priority`
- materially conflicting expectation-stage inputs => `uncertainty_conflict`
- insufficient or non-directional expectation-stage inputs => `insufficient_signal`

### Prompt and Output Shape

Milestone 5 should add one compact divergence section to downstream reasoning input.

Expected shape:

- `divergence_analysis`
- compact expected-vs-actual comparison
- enough detail to explain the mismatch without turning the prompt into a timeline dump

The divergence section should help the model explain why the market showed no material follow-through, overrode the apparent signal, or moved in the opposite direction.

Canonical divergence output should remain structured and deterministic.

Recommended minimum fields:

- `label`
- `expected_direction`
- `actual_direction`
- `actual_percent_move`
- `flat_threshold_percent`
- `signal_votes`
- `macro_confirmation`

Meaning:

- `label`: one of the milestone outcomes above
- `expected_direction`: `up`, `down`, or `none`
- `actual_direction`: `up`, `down`, or `flat`
- `actual_percent_move`: net bounded-window percent move
- `flat_threshold_percent`: threshold used to classify `flat`
- `signal_votes`: compact per-signal directional votes such as technical, context, and trajectory
- `macro_confirmation`: whether explicit monitored-set or shared-context evidence justified `competing_macro_priority`

User-facing prose may sit on top of this structure, but prose should not be the canonical divergence record. When LLM-generated presentation text is used, it should be returned in small display-oriented fields rather than one large text blob.

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

### Consumer Rollout

Milestone 5 may land asset-level divergence first, then extend the same contract to monitored-set consumers.

Meaning:

- asset-level divergence is the smallest complete first implementation
- monitored-set support should extend the same divergence contract rather than create a parallel system
- `competing_macro_priority` should only be emitted where explicit monitored-set or shared-context evidence is actually available
- absence of monitored-set evidence should not block shipment of the rest of the divergence classifier

### Validation and Review

Milestone 5 should be validated in two layers:

1. deterministic curated fixtures for code-level validation
2. a documented CLI inspection tool for live or current-scenario review

Fixture guidance:

- unit tests should use frozen curated fixtures as the regression source of truth
- synthetic fixtures are acceptable, but frozen real examples are preferred when they can be captured cleanly
- each fixture should include the classifier inputs and the expected deterministic outcome

CLI guidance:

- the CLI tool should print the divergence inputs, structured outputs, and presentation fields together so humans can judge whether the result is sensible
- once implemented, that tool should be documented in general project documentation, not only in roadmap notes, so it remains discoverable as an ongoing validation aid

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
