---
name: Narrative Continuity for Asset Context
description: Open ADR for bounded short-memory continuity in asset analysis
type: reference
---

# ADR

## ADR-002 Narrative Continuity for Asset Context

Status: Approved

## Roadmap Position

This ADR corresponds to Milestone 2 of the Autonomous Market Intelligence roadmap:

- [Autonomous Market Intelligence Roadmap](../roadmaps/00%20-%20autonomous-market-intelligence/roadmap.md)

Its role is narrow: add short-memory continuity to asset-level context so analysis can explain what changed across recent days, with ingestion-time headline sentiment as a strongly preferred companion signal.

It is not intended to solve portfolio intelligence, watchlists, sentiment trajectory, counterfactual reasoning, strategy validation, or autonomous trading.

## Context

ADR-001 broadens asset context beyond exact symbol mentions, but each analysis can still behave like an isolated snapshot.

That is not enough when users need answers such as:

- what is new today
- what is still driving the asset from prior days
- what changed in the story since the last analysis

Without bounded temporal continuity, the system can describe a set of headlines, but it cannot reliably distinguish a fresh catalyst from an ongoing narrative or a narrative shift.

## Decision

Milestone 2 should add a small continuity layer on top of the Milestone 1 asset context pack.

That layer should:

1. keep timestamps on all selected context items
2. look back across a short bounded window of recent selected items
3. classify each retained item as `new`, `continuing`, or `shifted`
4. provide a compact "story so far" summary section to the reasoning prompt

The continuity layer should stay deterministic and bounded. It should enrich asset analysis input. It should not become a durable narrative engine or a second reasoning system.

The first consumer remains the current asset-analysis path.

Future consumers may reuse the same continuity pattern later for:

1. portfolio monitoring
2. watched-assets monitoring
3. sentiment trajectory inputs

## Intended Shape

The future implementation should treat continuity as an extension of context building, not as an execution or recommendation layer.

Expected flow:

1. build the current asset context pack for `as_of`
2. retrieve retained selected context items for the same asset inside the short lookback window
3. compare recent retained items against the current pack
4. emit a compact continuity view for the prompt

That continuity view should remain small and auditable. It should not require replaying full historical prompts or storing narrative prose as a source of truth.

## Resolved Decisions

### Retention Window

Milestone 2 should use a short sliding lookback window.

Boundaries:

- default target: `5` days
- allowed range: `3-7` days
- items older than the configured window should be excluded rather than weakly retained forever

This milestone prefers a hard bounded window over decay heuristics because the simpler rule is easier to audit.

### Continuity Unit

The continuity unit should be the selected context item, not a full analysis output and not a raw provider payload dump.

Reason:

- selected items are already curated for relevance
- they are smaller than full prompt artifacts
- they keep the continuity layer aligned with Milestone 1 boundaries

Milestone 2 should not require durable storage of complete prompts or model responses just to support continuity.

### Required Temporal Fields

Each retained continuity item should support at least:

- stable identity or dedupe key
- asset identity
- timestamp
- source or provenance
- relevance basis or tags
- compact payload sufficient for prompt reuse

If the existing persisted news artifact already contains the needed timestamp fields, Milestone 2 should reuse it instead of creating a parallel news table.

### Narrative State Labels

Milestone 2 should use only three continuity labels:

- `new`
- `continuing`
- `shifted`

Meaning:

- `new`: relevant inside the current pack but not present in the recent retained set
- `continuing`: materially the same narrative item or cluster remains relevant across the window
- `shifted`: the same broad topic remains relevant, but the narrative direction, actor, or framing materially changed

This milestone should keep the state model small. Richer states belong in later milestones.

### Shift Detection Method

Milestone 2 should prefer deterministic shift detection before any LLM interpretation.

Expected signals may include:

- dedupe or cluster identity mismatch within the same topic family
- changed actor, event, or framing tags
- changed direction marker from the ingestion-time sentiment label

The LLM may explain the shift, but it should not be responsible for deciding whether a retained item exists at all.

### Prompt Shape

Milestone 2 should add one compact continuity section to the asset-analysis prompt.

Expected shape:

- `story_so_far`
- at most `3-5` compact bullets or items
- summarize only the strongest recent continuity signals

The continuity section should help the model answer "what changed?" without materially increasing prompt noise.

### Persistence Boundary

Milestone 2 may justify retaining compact continuity-ready item records across a short window, but it should not add a broad narrative-history system.

Allowed persistence for this milestone:

- timestamped selected context items or equivalent compact continuity artifacts
- optional ingestion-time headline sentiment labels when captured

Not approved in this milestone:

- full fact versioning
- long-lived narrative state tables
- stored narrative summaries as the canonical source of truth
- replay-oriented storage of raw prompts and responses

### Ingestion-Time Sentiment

Milestone 2 should capture basic headline sentiment at ingestion time unless implementation constraints make it materially infeasible inside the milestone window.

Allowed labels:

- `positive`
- `neutral`
- `negative`

Required direction for this milestone:

- sentiment should attach to the persisted headline artifact at ingestion time
- batch classification for multiple headlines in one LLM call is allowed when it reduces token or latency cost
- historical backfill is not required

Reason:

- it makes `shifted` detection more reliable when framing changes but topic overlap remains
- it creates a clean forward-only dataset for later sentiment trajectory work
- it avoids expensive and inconsistent retroactive reclassification later

This ADR does not approve sentiment aggregation or trajectory logic. That belongs to Milestone 4.

## Constraints

- Keep continuity bounded to a short explicit window.
- Keep selection and labeling deterministic before reasoning.
- Keep the prompt addition compact.
- Reuse existing news and context-selection artifacts where possible.
- Keep storage, reasoning, and execution concerns separate.

## Non-Goals

- Portfolio or watch-scope continuity
- Opportunity discovery
- Sentiment aggregation across days
- Sentiment trajectory states such as improving or deteriorating
- Counterfactual reasoning
- Trade recommendations
- Strategy approval logic
- Autonomous trading behavior

## Notes

This ADR should remain independently mergeable and user-releaseable when implemented.

Expected user-facing value:

- asset explanations can describe what changed across recent days instead of treating each analysis as a standalone snapshot

This is intentionally narrower than full narrative memory. It records the minimum continuity layer needed before later milestones add sentiment trajectory, portfolio/watch monitoring, or deeper reasoning.
