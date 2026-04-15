---
name: News Context Expansion
description: Open ADR for broadening AI news context beyond symbol-only headlines
type: reference
---

# ADR

## ADR-001 Open News Context Expansion

Status: Open

## Roadmap Position

This ADR corresponds to Milestone 1 of the Autonomous Market Intelligence roadmap:

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

## Open Questions

- Which fields should be treated as the primary source of sector and industry context when data is incomplete?
- Should thematic keyword mappings be hardcoded or stored as configuration?
- Should broad market news be fetched from the asset's market only, or also from cross-market macro sources?
- How many headlines should be allowed per context bucket before deduplication and ranking?
- What is the explicit prompt budget for the final asset context pack?

## Notes

This ADR should remain independently mergeable and user-releaseable when implemented.

Expected user-facing value:

- asset explanations improve when the relevant driver is sector, macro, or thematic news rather than a direct symbol mention

This is intentionally not part of the MLP scope. It records the target direction for a later incremental implementation while keeping the first milestone tightly bounded.
