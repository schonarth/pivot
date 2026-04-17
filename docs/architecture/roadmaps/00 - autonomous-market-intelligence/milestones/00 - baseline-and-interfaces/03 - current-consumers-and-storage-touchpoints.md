# 03 - Current Consumers and Storage Touchpoints

## Purpose

Map current consumers and likely storage touchpoints so Milestone 01 can integrate with the right parts of the system and avoid duplicate structures.

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
- 02 - shared-vocabulary-and-interface-contracts.md

## Likely Files Touched

- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces/03 - current-consumers-and-storage-touchpoints.md
- backend/*
- frontend/*

## Entry Conditions

- baseline vocabulary drafted
- current-state scan drafted

## Background

Milestone 01 should improve the current asset-analysis consumer first, but later milestones will likely expand to portfolio, watched assets, and strategy validation. Before building anything, the project needs a clear view of who consumes context today and which data should remain transient versus which data may later justify storage.

## Detailed Requirements

- identify the current consumer that Milestone 01 is improving
- list the near-term roadmap consumers in dependency order where possible
- identify likely storage touchpoints for:
  - news metadata
  - context artifacts
  - technical signals
  - analysis outputs
- distinguish between:
  - data that should likely stay transient in early milestones
  - data that may justify persistence later
- identify risks of creating duplicate storage or duplicate prompt-building paths
- avoid introducing schemas or migrations in this task

## Proposed Approach

- derive the current consumer from the actual implementation path, not only from the roadmap
- list future consumers only where they materially affect architectural choices
- frame storage notes as touchpoints and boundaries, not final schema design
- prefer a simple table or bullet map that later tasks can reuse directly

## Validation Scenarios

- a Milestone 01 implementation task should be able to identify its current consumer immediately from this file
- a later portfolio or watch milestone should be able to see whether it is expected to reuse or extend the same context path
- if stored news artifacts are not yet justified, this file should say so explicitly to prevent accidental overbuilding
- if duplicate storage paths are a likely risk, they should be called out concretely enough to guide code review

## Task Steps

1. Identify the current consumer for asset-level analysis.
2. List probable near-term consumers:
   - asset analysis
   - portfolio monitoring
   - watched-assets monitoring
   - strategy validation
3. Identify where context, analysis artifacts, news metadata, and technical signals likely belong if stored.
4. Note what should remain transient until later milestones prove persistent storage is needed.
5. Call out duplication risks if multiple milestones create separate storage or prompt-building paths.

## Current Consumer

Primary Milestone 01 consumer:

- per-asset AI insight
  - first-party UI path:
    - `frontend/src/components/AssetAnalysisTab.vue`
    - `GET /api/assets/:id/ai-insight`
  - agent-facing path:
    - `POST /api/mcp/asset-insight/`
  - shared backend implementation:
    - `backend/ai/services.py` `AIService.analyze_asset`

This is the current user-visible analysis consumer Milestone 01 should improve first.

## Near-Term Consumers in Roadmap Order

1. Asset analysis
   - current live consumer
   - direct Milestone 01 dependency
2. Portfolio monitoring
   - future portfolio-level context and prioritization
   - likely reuses asset-level context selection plus portfolio state
3. Watch monitoring
   - future watched-assets scope without open positions
   - should reuse the same context-selection vocabulary, not create a separate prompt path
4. Strategy validation
   - future bounded reasoning about whether a setup should be approved or rejected
   - should remain separate from autonomous execution

## Storage Touchpoints

### News metadata

Current touchpoint:

- `backend/markets/models.py` `NewsItem`

What belongs here today:

- headline
- summary
- source
- URL
- asset link
- fetched/published timestamps
- optional sentiment score

Milestone 00 guidance:

- continue treating `NewsItem` as the current persisted source artifact for asset-scoped news retrieval
- avoid creating a second persisted news artifact path in Milestone 01

### Technical signals

Current touchpoints:

- raw history:
  - `backend/markets/models.py` `OHLCV`
- optional persisted snapshot:
  - `backend/markets/models.py` `TechnicalIndicators`

What belongs here today:

- market history in `OHLCV`
- reusable derived indicators only when there is a clear reuse case

Milestone 00 guidance:

- `OHLCV` is the durable source of truth for technical derivation
- `TechnicalIndicators` may hold reusable snapshots, but Milestone 01 should not introduce parallel technical-signal stores

### Context artifacts

Current touchpoint:

- none as a durable model

Current behavior:

- context is assembled transiently inside `AIService.analyze_asset`

Milestone 00 guidance:

- keep context packs transient in early milestones
- do not add persisted prompt-time context tables until retrieval, reuse, or audit needs are proven

### Analysis outputs

Current touchpoints:

- transient response from `AIService.analyze_asset`
- cached copy in Django cache for 24 hours via `cache.set(...)`

Milestone 00 guidance:

- treat current insight output as transient plus cache-backed
- do not add durable analysis-output tables in Milestone 01 unless later milestones require replay, audit history, or temporal continuity

## Transient vs Persistent Guidance

Keep transient for now:

- prompt-time context packs
- ranked context selections
- per-request reasoning scaffolds
- LLM raw prompt/response artifacts unless an explicit audit requirement appears

Reasonable to persist now or continue persisting:

- raw or normalized market history in `OHLCV`
- fetched asset-scoped news metadata in `NewsItem`
- reusable technical indicator snapshots in `TechnicalIndicators`
- strategy/backtest execution records already modeled outside the analysis path

May justify persistence later:

- continuity artifacts across days
- scored and deduplicated context selections
- analysis history for audit and change-tracking
- watch-scope or portfolio-scope monitoring state

## Duplication Risks

- Prompt-building duplication:
  - current prompt assembly lives in `AIService.build_indicator_insight_prompt`
  - future milestones should not create one-off prompt builders per consumer for the same asset-analysis task
- Technical-calculation duplication:
  - `AssetViewSet.indicators` recalculates indicator series inline while `IndicatorCalculator` computes a latest snapshot elsewhere
  - later milestones should extend one technical-analysis boundary, not both independently
- News-storage duplication:
  - `NewsItem` already exists
  - Milestone 01 should avoid adding a second asset-news store for expanded context unless the existing model proves insufficient
- Consumer-path duplication:
  - frontend and MCP already share `AIService.analyze_asset`
  - new asset-analysis behavior should continue to converge on one backend analysis path

## Tests to Add or Update

- docs-only baseline task
- no direct unit tests expected unless code changes are introduced to preserve current consumers

## Commands to Run

- if code is touched: run relevant lint, typecheck, and affected tests

## Exit Conditions

- current consumer is explicitly named
- likely future consumers are listed in roadmap terms
- likely storage touchpoints are documented with boundaries
- transient versus persistent data concerns are called out

## Implementation Notes / What Was Done

Named the current per-asset insight consumer, listed roadmap-near consumers in dependency order, and documented which artifacts should stay transient versus where persistence already exists. Added concrete duplication risks so Milestone 01 can extend one path instead of creating parallel prompt, signal, or storage flows.

## Open Follow-Ups

- see Deferred Improvements `002 - Persisted News Artifacts Beyond Prompt-Time Assembly`
