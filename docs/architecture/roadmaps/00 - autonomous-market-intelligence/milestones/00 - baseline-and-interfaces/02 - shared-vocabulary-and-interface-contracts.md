# 02 - Shared Vocabulary and Interface Contracts

## Purpose

Define shared terms and minimum interface contracts so later roadmap milestones use the same language and integration points.

## Roadmap Milestone

Milestone 00 - Baseline and Interfaces

## Governing ADR

Roadmap-only planning task for Milestone 00 baseline work.

## Status

done

## Owner

GPT-5.4 / docs

## Branch

feat/autonomous/00-baseline

## Date Started

2026-04-15

## Date Completed

2026-04-15

## Dependencies

- 00 - milestone coordination.md
- 01 - boundary-decision-and-current-state-scan.md

## Likely Files Touched

- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces/02 - shared-vocabulary-and-interface-contracts.md
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/roadmap.md
- docs/architecture/adrs/ADR-001-open-news-context-expansion.md

## Entry Conditions

- baseline boundary scan complete
- current consumers identified

## Background

The roadmap now spans asset analysis, portfolio monitoring, watch functionality, strategy validation, and autonomous execution. Those later milestones will become harder to coordinate if they use overlapping words with different meanings. This task creates a small shared language and minimum interface assumptions so later ADRs and implementation specs stop arguing about basic terms.

## Detailed Requirements

- define a compact vocabulary for the scopes already named by the roadmap:
  - asset scope
  - portfolio scope
  - watch scope
  - strategy scope
- define core objects used across milestones:
  - context item
  - context pack
  - analysis input
  - analysis output
- define minimal contracts for:
  - what the context builder receives
  - what it returns
  - what the reasoning layer consumes
  - what execution layers must not infer implicitly
- keep these contracts narrow enough that Milestone 01 is not overdesigned
- avoid locking in database schemas or API payloads prematurely unless the codebase already forces them

## Proposed Approach

- reuse the boundary language established in the previous task
- align terms with the roadmap and ADR-001 instead of creating a second vocabulary
- prefer short definitions and field lists over long prose
- call out optional versus required fields where uncertainty remains
- document explicit non-assumptions if later milestones are expected to refine a contract

## Validation Scenarios

- a Milestone 01 task should be able to say “context pack” and have one agreed meaning
- a future portfolio milestone should be able to reuse “context item” without redefining it
- an execution-layer task should be able to identify which outputs are analysis artifacts versus actionable decisions
- the vocabulary should be small enough that an agent can hold it in working memory without carrying the whole roadmap

## Task Steps

1. Define a compact vocabulary for:
   - asset scope
   - portfolio scope
   - watch scope
   - strategy scope
   - context item
   - context pack
   - analysis output
2. Define minimum contracts for later milestones:
   - what a context builder receives
   - what a context builder returns
   - what an analysis layer consumes
   - what execution layers must not assume
3. Keep contracts technology-agnostic where possible.
4. Avoid overdesigning fields that later milestones have not validated yet.
5. Cross-check the vocabulary against ADR-001 and roadmap language.

## Shared Vocabulary

### Scope terms

- Asset scope:
  - one asset as the unit of context selection and analysis
  - current concrete example: one `markets.models.Asset`
- Portfolio scope:
  - the set of assets, cash state, and risk state attached to one portfolio
  - may include held positions, cash constraints, and portfolio guardrails
- Watch scope:
  - a monitored set of assets without requiring an open position
  - not yet implemented as a first-class model in the codebase
  - reserved roadmap scope, not a Milestone 00 schema commitment
- Strategy scope:
  - the bounded decision frame for one strategy instance, including rule settings, monitored assets, and approval state
  - current concrete example: one `strategies.models.StrategyInstance`

### Cross-milestone objects

- Context item:
  - one selected input fact used for reasoning
  - examples: one headline, one technical snapshot, one market-status datum
  - should carry provenance and scope tags
- Context pack:
  - the bounded set of context items prepared for one reasoning request
  - may include compact summary metadata, but is not itself the final analysis
- Analysis input:
  - the full payload handed from context selection to reasoning
  - includes target scope, target identifiers, context pack, and any reasoning constraints
- Analysis output:
  - the structured artifact returned by reasoning
  - examples: explanation, confidence, recommendation, scenario summary
  - not equivalent to an execution command

## Minimum Interface Contracts

### Context builder input

Required:

- `scope_type`
  - one of `asset`, `portfolio`, `watch`, `strategy`
- `scope_id` or equivalent target identity
- `as_of`
  - evaluation time boundary

Optional:

- `asset_ids`
- `portfolio_id`
- `max_items`
- `lookback_window`
- `include_types`
  - such as `news`, `technical`, `market`, `position`

Non-assumptions:

- does not require a fixed database schema
- does not require a single provider for news or technical data
- does not imply prompt text formatting

### Context builder output

Required:

- `scope_type`
- `scope_id`
- `as_of`
- `items`
  - array of context items

Each context item should minimally support:

- `item_type`
- `source`
- `provenance`
- `relevance_basis`
- `timestamp` or `date`
- `payload`

Optional:

- `asset_id`
- `market`
- `tags`
- `rank`
- `dedupe_key`

Non-assumptions:

- no required persistence
- no commitment yet to typed DTOs in code
- no commitment that all item types share identical payload fields

### Reasoning-layer input

Required:

- one explicit analysis target
- one explicit context pack
- one explicit task intent
  - examples: `asset_insight`, `portfolio_summary`, `watch_monitor`, `strategy_validation`

Reasoning may:

- summarize
- compare
- prioritize
- produce bounded recommendations or scenarios

Reasoning must not:

- fetch broad unbounded context on its own
- mutate persistent portfolio state
- imply trade approval from narrative confidence alone

### Execution-layer constraints

Execution layers must require explicit structured inputs beyond free-form analysis text.

Execution layers must not assume:

- any `BUY` or `SELL` string inside an analysis artifact is automatically actionable
- absence of contradictory news is trade approval
- high-confidence analysis bypasses guardrails, budgets, approvals, or permissions

Execution layers may consume:

- approved strategy state
- deterministic alert thresholds
- validated structured recommendation records added by later milestones

## Contract Alignment to Current Code

- Current asset analysis target:
  - one `Asset`
- Current context sources:
  - `NewsItem`
  - `OHLCV`
  - latest derived indicators
- Current reasoning output shape:
  - `recommendation`
  - `confidence`
  - `technical_summary`
  - `news_context`
  - `price_target`
  - selected `news_items`

This current shape is a valid Milestone 00 example of an analysis output, but not the only future contract.

## ADR and Roadmap Alignment Notes

- Matches roadmap language: asset, portfolio, watch, strategy
- Preserves ADR-facing separation between context expansion and later decisioning
- Stays narrow enough for Milestone 01 without locking in schema or transport choices

## Tests to Add or Update

- docs-only baseline task
- no direct unit tests expected unless code is touched to formalize interfaces

## Commands to Run

- if code is touched: run relevant lint, typecheck, and affected tests

## Exit Conditions

- shared vocabulary is unambiguous
- later milestones can reference one common set of terms
- minimum contracts exist for context input and output without locking in premature implementation detail

## Implementation Notes / What Was Done

Defined the shared vocabulary around scope, context items, context packs, analysis input, and analysis output. Added minimal contracts that fit the current asset-analysis path while staying technology-agnostic enough for Milestones 01+.

## Open Follow-Ups

- see Deferred Improvements `003 - Typed Context Pack Contract`
