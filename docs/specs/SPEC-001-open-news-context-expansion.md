---
name: News Context Expansion
description: Spec for broadening AI news context beyond symbol-only headlines
type: reference
---

# SPEC

## SPEC-001 Open News Context Expansion

Status: Approved
Governing ADR: [ADR-001-deterministic-context-selection](../adrs/ADR-001-deterministic-context-selection.md)

## Roadmap Position

This SPEC corresponds to Milestone 1 of the Autonomous Market Intelligence roadmap:

- [Autonomous Market Intelligence Roadmap](../roadmaps/00%20-%20autonomous-market-intelligence/roadmap.md)

Its role is narrow: improve asset-level context selection.

It is not intended to solve narrative memory, strategy reasoning, portfolio intelligence, watchlists, opportunity discovery, or autonomous trading.

## Context

AI prompts that explain portfolio or asset behavior are currently too dependent on headlines that mention the exact asset symbol. That works for some names, but it misses the broader drivers that often matter more in practice.

For example, `PETR4` is influenced not only by Petrobras-specific news, but also by oil prices, OPEC decisions, geopolitical shocks, Brazil macro policy, currency moves, and other sector-level events.

## Decision

The desired direction is to expand news selection so each asset can gather a small, relevant context set from:

1. Symbol-level news
2. Company-name news
3. Sector-level news
4. Industry-level news
5. Market or macro news tied to the asset
6. A small set of thematic keywords for known sectors

The prompt should receive a curated, deduplicated list of headlines rather than a large unfiltered dump.

The Milestone 01 implementation should use deterministic context selection, deduplication, and ranking rules rather than an LLM-driven retrieval loop.

This context builder is intended to support the current asset-analysis consumer first.

Future consumers may reuse the same pattern later for:

1. portfolio-level monitoring
2. watched-assets monitoring
3. strategy validation

## Intended Shape

The future implementation should add a lightweight context-building step before model calls. That step can produce tagged headlines such as:

- `symbol`
- `company`
- `industry`
- `sector`
- `macro`
- `theme`

The model should then see enough surrounding context to explain why an asset may move even when the exact symbol is absent from the headlines.

The output of this step should remain a compact asset context pack, not a full reasoning or recommendation layer.

## Resolved Decisions

### Sector and Industry Fallback Priority

When sector or industry metadata is incomplete, Milestone 01 should prefer correctness over maximum coverage.

Fallback order:

1. existing asset metadata stored in the project
2. small explicit project overrides for known gaps or mistakes
3. if still unresolved, skip sector or industry expansion rather than infer loosely

This SPEC does not approve LLM-based sector or industry inference for Milestone 01.

### Thematic Keyword Storage

Thematic keyword mappings should not be hardcoded directly into implementation logic and should not be stored in the database in Milestone 01.

For Milestone 01 they should live in a small, versioned policy artifact in the codebase.

Milestone 01 thematic mappings should stay limited to broad, relatively stable themes. Highly time-sensitive relevance should be deferred to later roadmap work.

### Local-Market and Cross-Market Macro Scope

Broad market news should not be limited only to the asset's own market.

Milestone 01 should:

1. fetch macro context from the asset's own market by default
2. allow cross-market macro context only when it is deterministically relevant to the asset's sector, industry, or durable themes

This keeps context local-first while still allowing globally relevant drivers such as commodities, rates, or durable macro exposure.

### Headline Caps Before and After Ranking

Milestone 01 should use small bucket-specific raw candidate caps before deduplication and ranking.

After deduplication and ranking:

- every bucket may contribute up to `0-2` survivors
- no bucket has a guaranteed quota
- a second survivor from the same bucket should only remain if it adds distinct informational value rather than repeating the same narrative

### Prompt Budget for Final Asset Context Pack

Milestone 01 should keep the final asset context pack compact.

Budget:

- soft target: `6-10` context items
- hard cap: `12` context items
- each bucket may contribute at most `2`
- no bucket is required to contribute

Each retained item should stay compact and should not become a mini-summary or reasoning block in this milestone.

### Deduplication and Ranking Method

Milestone 01 should keep deduplication and ranking deterministic.

Expected flow:

1. collect candidates by bucket
2. normalize candidates
3. deduplicate or cluster obvious duplicates
4. rank deterministically
5. keep the strongest survivors within the prompt budget

The LLM should consume the curated result, not decide the curation result.

### Weak and Clickbait Headlines

Milestone 01 should aggressively rank down weak or clickbait headlines.

Preference order:

- direct, content-rich headlines
- headlines with concrete actors, events, numbers, or causal language

Penalize:

- teaser framing
- vague reaction framing
- low-information headlines that hide the actual event

If this results in thinner context packs for some assets, that is acceptable for Milestone 01. Better handling of article-body signal can be revisited later if needed.

## Constraints

- Keep the prompt small and focused.
- Prefer deterministic rules over complex retrieval.
- Avoid broadening so much that unrelated news drowns out the signal.
- Preserve the current asset-specific prompt structure.
- Keep storage, reasoning, and execution concerns separate.

## Non-Goals

- Multi-day narrative tracking
- Sentiment trajectory
- Counterfactual or expected-vs-actual reasoning
- Trade recommendations
- Scenario generation
- Portfolio-level aggregation
- Watched-assets support
- Opportunity discovery
- Autonomous trading behavior

## Notes

This SPEC should remain independently mergeable and user-releaseable when implemented.

Expected user-facing value:

- asset explanations improve when the relevant driver is sector, macro, or thematic news rather than a direct symbol mention

This is intentionally not part of the MLP scope. It records the target direction for a later incremental implementation while keeping the first milestone tightly bounded.
