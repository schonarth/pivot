---
name: Context Scope Expansion
description: Spec for expanding context building from single assets to portfolio and watch scopes
type: reference
---

# SPEC

## SPEC-003 Context Scope Expansion: Asset, Portfolio, Watchlist

Status: Approved
Governing ADR: [ADR-003-shared-pipeline-for-monitored-sets](../adrs/ADR-003-shared-pipeline-for-monitored-sets.md)

## Roadmap Position

This SPEC corresponds to Milestone 3 of the Autonomous Market Intelligence roadmap:

- [Autonomous Market Intelligence Roadmap](../roadmaps/00%20-%20autonomous-market-intelligence/roadmap.md)

Its role is narrow: generalize context building and analysis input from one asset to a user-defined monitored set.

It is not intended to solve discovery of new assets, sentiment trajectory, strategy validation, or autonomous trading.

## Context

SPEC-001 improves asset-level context selection. SPEC-002 adds bounded temporal continuity for one asset.

That is still too narrow for users who think in monitored sets:

- one portfolio with multiple held positions
- one watchlist with assets worth monitoring before entry
- one macro or sector event affecting several assets at once

Without a portfolio and watch scope, the system forces users to inspect assets one by one and mentally deduplicate the same event across several analyses.

## Decision

Milestone 3 should expand the context-builder boundary so the same underlying pipeline can support:

1. one asset
2. one portfolio
3. one watch set

The system should treat portfolio and watch intelligence as scoped views over a monitored asset set, not as separate bespoke prompt paths.

Milestone 3 should also introduce clustered shared-event handling so macro or sector stories affecting multiple monitored assets appear once with affected assets attached, instead of repeating as near-duplicate per-asset entries.

The first new consumers should be:

1. portfolio summary or monitoring
2. watch summary or monitoring

Future milestones may reuse the same scope-expansion pattern later for:

1. opportunity discovery outputs that populate watch scope
2. strategy validation over a monitored asset set

## Intended Shape

The future implementation should build one context-selection pipeline that accepts the same core contract from Milestone 00:

- `scope_type`
- `scope_id`
- `as_of`

Expected behavior by scope:

1. `asset`
   - context pack centered on one asset
2. `portfolio`
   - context pack across held assets plus portfolio-level shared events
3. `watch`
   - context pack across watched assets without requiring open positions

The resulting analysis input should preserve asset-level detail while also exposing shared events at the monitored-set level.

Milestone 3 should not require one entirely separate reasoning stack for each scope.

## Resolved Decisions

### Watch Scope Definition

Milestone 3 should treat watch scope as a first-class monitored asset set that does not require an open position.

Minimum expectations:

- a watch scope contains explicit user-selected assets
- watch scope is distinct from portfolio holdings
- the same asset may appear in both a portfolio scope and a watch scope

This SPEC defines the product concept. It does not require a specific database schema in the SPEC itself.

### Shared Pipeline Over Separate Prompt Paths

Milestone 3 should extend the existing asset-analysis path rather than creating separate one-off pipelines for asset, portfolio, and watch intelligence.

Reason:

- it preserves one context vocabulary
- it reduces duplication in selection, deduplication, and continuity handling
- it makes later milestones easier to apply across scopes

Scope-specific behavior should come from inputs and summarization shape, not from fully separate retrieval systems.

### Monitored Set Membership

For this milestone, monitored-set membership should be explicit and deterministic.

Portfolio membership:

- assets currently held in the portfolio

Watch membership:

- assets explicitly attached to the watch scope

Not approved in this milestone:

- inferred watched assets
- automatically discovered assets
- ranking-based scope population

Those belong to later discovery work.

### Shared Event Clustering

Milestone 3 should cluster shared stories when one event affects multiple assets in the same monitored set.

Examples:

- one oil-sector story affecting several Brazilian oil names
- one rates story affecting several financial holdings
- one macro currency story affecting multiple export-sensitive assets

Clustered events should:

- appear once in the monitored-set view
- list affected assets explicitly
- preserve per-asset relevance tags where needed

The goal is to remove duplicate noise, not to erase asset-specific detail.

### Cluster Eligibility

Milestone 3 should only cluster events when duplication is obvious and materially overlapping.

Expected eligibility signals may include:

- same dedupe key or same source story family
- same macro, sector, industry, or theme tags
- multiple monitored assets linked to the same retained event

If overlap is weak or ambiguous, the system should prefer separate items over aggressive clustering.

### Portfolio-Level Prioritization

Milestone 3 should support deterministic prioritization of events at the monitored-set level.

Priority should prefer events that:

- affect multiple monitored assets
- affect larger positions within a portfolio
- are more recent
- survive existing asset-level ranking and continuity filters

This milestone should prioritize importance within the monitored set. It should not produce trade advice or approval logic.

### Asset Detail Preservation

Milestone 3 should preserve the ability to drill from monitored-set intelligence back to asset-level context.

Expected shape:

- one monitored-set summary view
- clustered shared events with affected assets
- asset-specific items that remain unique to one asset

A portfolio or watch summary should never flatten away which assets are actually implicated.

### Continuity Reuse

If SPEC-002 continuity artifacts exist, Milestone 3 should reuse them within each asset before composing the monitored-set view.

Meaning:

- continuity remains asset-bounded first
- clustering happens after asset-level context selection
- Milestone 3 does not introduce cross-asset narrative state as a separate system

This keeps Milestone 3 aligned with earlier boundaries and avoids inventing a portfolio-level narrative engine too early.

### Persistence Boundary

Milestone 3 may justify limited monitored-set state, but it should avoid broad new storage systems unless they are required by the consumer.

Reasonable persistence for this milestone may include:

- watch-scope membership
- minimal monitored-set metadata

Not approved in this milestone:

- discovery candidate stores
- durable portfolio intelligence history as a new canonical record
- separate duplicated news stores for portfolio or watch scope

Context packs and clustering artifacts should remain transient unless short-lived reuse is clearly required.

## Constraints

- Keep one shared context vocabulary across `asset`, `portfolio`, and `watch`.
- Keep monitored-set membership explicit.
- Prefer deterministic clustering and prioritization.
- Avoid duplicate macro or sector stories across the same monitored set.
- Preserve asset-level traceability inside monitored-set summaries.
- Keep storage, reasoning, and execution concerns separate.

## Non-Goals

- Discovery of assets not already held or watched
- Automatic watchlist population
- Sentiment trajectory across the monitored set
- Cross-asset causal inference beyond bounded clustering
- Trade recommendations
- Strategy approval logic
- Autonomous trading behavior

## Notes

This SPEC should remain independently mergeable and user-releaseable when implemented.

Expected user-facing value:

- portfolio and watch monitoring become first-class
- shared stories appear once instead of repeating per asset
- users can see which monitored assets are affected without manually comparing multiple asset reports

This milestone expands scope, not autonomy. It reuses the asset-analysis foundation so later milestones can add sentiment trajectory, discovery, and strategy logic on top of the same monitored-set boundary.
