---
name: Sentiment Trajectory and Narrative State
description: Open ADR for tracking sentiment direction over time for assets and themes
type: reference
---

# ADR

## ADR-004 Sentiment Trajectory and Narrative State

Status: Approved

## Roadmap Position

This ADR corresponds to Milestone 4 of the Autonomous Market Intelligence roadmap:

- [Autonomous Market Intelligence Roadmap](../roadmaps/00%20-%20autonomous-market-intelligence/roadmap.md)

Its role is narrow: add a short-window trajectory layer so analysis can explain whether sentiment is improving, deteriorating, conflicting, or reversing for important assets and themes.

It is not intended to authorize trading, replace context selection, or create a long-horizon prediction engine.

## Context

ADR-001 broadens context selection. ADR-002 adds bounded continuity for one asset. ADR-003 expands that context to portfolio and watch scopes.

That still leaves a gap: the system can retain relevant items and label them as `new`, `continuing`, or `shifted`, but it cannot yet explain the direction of sentiment across those retained items.

Users eventually need answers such as:

- is the narrative improving or deteriorating
- are headlines conflicting even when the same topic remains active
- did sentiment reverse even though the topic did not disappear
- is price action diverging from the recent tone of coverage

Without a bounded trajectory layer, the system can describe recent context, but it cannot reliably summarize directional sentiment change across the short historical window.

## Decision

Milestone 4 should add a deterministic short-window sentiment-trajectory layer on top of the selected context items retained for continuity.

That layer should:

1. reuse per-item sentiment labels when they exist
2. compute compact trajectory signals for assets and themes across a bounded recent window
3. support at least these states:
   - `improving`
   - `deteriorating`
   - `conflicting`
   - `reversal`
4. expose the resulting trajectory summary as analysis input, not as execution logic

The trajectory layer should stay small, auditable, and forward-looking only within the short retained window. It should not become a durable market-opinion engine or a trade-decision system.

The first consumers should be:

1. asset analysis
2. monitored-set analysis where Milestone 3 scope expansion exists

Implementation priority:

- asset-scope trajectory should land first
- the same trajectory contract should also be applied to monitored-set consumers when Milestone 3 outputs are implementation-ready and doing so does not require new monitored-set surface design
- if monitored-set support is not implementation-ready at execution time, Milestone 4 should not be blocked from shipping clean asset-scope trajectory first

Future milestones may reuse the same trajectory signals later for:

1. divergence reasoning
2. opportunity discovery
3. strategy validation

## Intended Shape

The future implementation should treat sentiment trajectory as an enrichment of selected context items, not as a replacement for context selection or continuity.

Expected flow:

1. build the current context pack
2. reuse the short-window retained items already available for continuity
3. read per-item sentiment labels for the retained items
4. aggregate compact trajectory signals by asset and, when useful, by theme
5. emit a small trajectory summary section for downstream reasoning

The trajectory summary should remain compact and bounded. It should not require storing full historical prompts or free-form narrative summaries as the system of record.

## Resolved Decisions

### Continuity Dependency

Milestone 4 should build on the short-window retained-item pattern established earlier rather than introducing a second historical tracking system.

Meaning:

- the trajectory layer should reuse continuity-ready retained items
- the same bounded window should be the default source of truth for recent sentiment direction
- Milestone 4 should not introduce a parallel long-range sentiment history store

### Sentiment Unit

The trajectory unit should remain the selected context item.

Reason:

- selected items are already relevance-filtered
- item-level sentiment is more auditable than direct document-set scoring
- it preserves alignment with the Milestone 1 and Milestone 2 context boundaries

### Allowed Base Sentiment Labels

Milestone 4 should assume the per-item sentiment vocabulary remains:

- `positive`
- `neutral`
- `negative`

This milestone may derive trajectory states from those labels and recent ordering. It should not expand the base sentiment taxonomy yet.

### Required Trajectory States

Milestone 4 should support at least:

- `improving`
- `deteriorating`
- `conflicting`
- `reversal`

Meaning:

- `improving`: recent retained sentiment became more positive over the bounded window
- `deteriorating`: recent retained sentiment became more negative over the bounded window
- `conflicting`: materially relevant retained items point in opposing directions without a clear dominant move
- `reversal`: the recent direction materially flipped from the prior retained direction

This milestone should keep the state model small and interpretable.

### Aggregation Scope

Milestone 4 should allow trajectory aggregation at two levels:

1. per asset
2. per theme when the same theme appears across retained items

Theme aggregation should be allowed only when theme tagging is explicit enough to keep the result auditable.

For this milestone, theme-level trajectory should require:

- the same explicit normalized theme tag on the relevant retained items
- cross-asset evidence from more than one asset inside the bounded window

A single asset with several retained items on the same theme is still asset trajectory, not theme trajectory.

If theme linkage is weak, the system should prefer asset-level trajectory over broad theme aggregation.

### Detection Method

Milestone 4 should prefer deterministic scoring and thresholding before any LLM explanation.

Expected input signals may include:

- ordered sequence of retained item sentiment labels
- recency weighting inside the bounded window
- theme or topic family tags
- continuity labels such as `new`, `continuing`, or `shifted`

The LLM may explain the trajectory, but it should not be responsible for inventing the underlying state.

### Window and Retention

Milestone 4 should stay inside a short explicit retention window derived from the continuity layer.

Preferred direction:

- default target: reuse the existing short window from continuity
- older items outside that window should not materially influence trajectory state

This milestone should favor a strict recent-history view over loosely weighted long-term memory.

### Prompt Shape

Milestone 4 should add one compact trajectory section to downstream reasoning input.

Expected shape:

- `sentiment_trajectory`
- compact per-asset or per-theme entries
- enough detail to explain directional change without turning the prompt into a timeline dump

The trajectory section should help the model explain directional context, especially when price action diverges from headline tone.

When evidence is insufficient or non-directional:

- Milestone 4 should not add a fifth canonical trajectory state
- no trajectory state should be emitted
- user-facing consumers may optionally render lightweight fallback language such as `no clear direction` or `not enough recent input` only when that adds explanatory value
- fading or disappearing signal may later inform broader narrative-lifecycle reasoning, but it is not a Milestone 4 trajectory state

### Persistence Boundary

Milestone 4 should compute trajectory on read from retained items and per-item sentiment labels.

Allowed persistence for this milestone:

- per-item sentiment labels on retained context items

Allowed optimization:

- thin ephemeral non-canonical caching only when it remains a pure optimization layer and can be dropped without affecting correctness or auditability

Not approved in this milestone:

- long-horizon sentiment history as a new canonical store
- persisted derived trajectory artifacts as a new canonical record
- portfolio-level execution signals derived directly from trajectory
- model-generated prose as the canonical sentiment record

### Execution Boundary

Milestone 4 should expose trajectory as analysis input only.

Not approved in this milestone:

- direct trade approval from sentiment trajectory alone
- autonomous trade triggers from sentiment states
- strategy execution side effects

Those belong to later milestones.

## Constraints

- Keep trajectory bounded to a short explicit window.
- Keep sentiment derivation auditable from retained items.
- Prefer deterministic aggregation before reasoning.
- Reuse existing context and continuity artifacts where possible.
- Keep analysis enrichment separate from execution.

## Non-Goals

- Direct trade execution from sentiment alone
- Long-horizon sentiment forecasting
- Complex ML training loops
- Full portfolio strategy logic
- Unbounded theme graph construction

## Notes

This ADR should remain independently mergeable and user-releaseable when implemented.

Expected user-facing value:

- analysis can explain whether the recent narrative is improving, deteriorating, conflicting, or reversing instead of presenting only static item sentiment
