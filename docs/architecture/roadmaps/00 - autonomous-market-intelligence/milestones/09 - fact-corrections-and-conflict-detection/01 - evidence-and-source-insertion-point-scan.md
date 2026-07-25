# 01 - Evidence and Source Insertion Point Scan

## Purpose

Identify the smallest safe insertion points for canonical source identity, correction records, deterministic treatment, recommendation invalidation, UI review, and MCP parity.

## Roadmap Milestone

Milestone 09 - Fact Corrections and Conflict Detection

## Governing SPEC

SPEC-009 Fact Corrections and Conflict Detection

## Status

done

## Owner

Codex / implementation

## Date Started

2026-07-25

## Date Completed

2026-07-25

## Branch

feat/autonomous/09-fact-corrections

## Dependencies

- `00 - milestone coordination.md`

## Likely Files Touched

- `backend/markets/models.py`
- `backend/markets/services.py`
- `backend/ai/models.py`
- `backend/ai/services.py`
- `backend/ai/strategy_validation.py`
- `backend/ai/views.py`
- `backend/mcp/*`
- `frontend/src/views/TradeNewView.vue`
- `frontend/src/api/ai.ts`
- `frontend/src/types/index.ts`

## Entry Conditions

- milestone coordination and required prior references read
- current `NewsItem`, context-selection, recommendation, scenario, frontend review, and MCP paths available for inspection

## Background

The milestone must extend existing evidence flows, not create a parallel fact-checking workspace or recommendation stack. Existing source text (`rss_feed` included), context selection, recommendation snapshots, and review consumers must be mapped before persistence contracts are added.

## Detailed Requirements

- map current source fields, ingestion paths, and all known source labels/feed URLs
- map recommendation context snapshot structure and the reverse lookup needed to find recommendations containing an artifact
- map source-quality calculation and its safe extension point
- map recommendation and scenario review API/UI consumers
- map MCP authentication, operator scope, and assistant identity propagation
- identify a platform-controlled source-artifact excerpt/value extraction path for immutable `original_value`
- record concrete gaps or blockers; do not invent contracts during the scan

## Task Steps

1. Scan the named backend and frontend paths plus their tests.
2. Trace one news artifact from ingestion through bounded context selection and stored recommendation evidence.
3. Trace one recommendation through API, strategy review, and scenario review surfaces.
4. Trace one authenticated MCP request through scope enforcement and audit identity.
5. Document the chosen insertion points in this task's implementation notes before dependent implementation begins.
6. Add tests only if correcting a discovered scan defect requires code changes.
7. Run focused verification for any changed code.

## Tests to Add or Update

- none expected unless scan findings require a corrective code change

## Commands to Run

- `cd backend && pytest ai/test_context.py ai/test_strategy_validation.py markets/test_services.py mcp/test_views.py`
- `cd frontend && npm run typecheck`

## Exit Conditions

- canonical insertion points and data ownership are explicit
- known legacy source mappings are enumerated
- immutable-original-value extraction source is identified
- invalidation lookup and UI/MCP parity paths are identified
- any blocker is concrete and escalated

## Implementation Notes / What Was Done

- Canonical source insertion: add `NewsSource` as the active relation on `markets.NewsItem`; retain `NewsItem.source` only as historical provenance. `NewsService` is the sole current ingestion writer (`_fetch_*` -> `_normalize_news_item` -> `_store_news_items`), so it must resolve the source before `update_or_create`. Current labels: `google_news_rss`, `yahoo_finance`, `marketwatch`, `valor_economico`, `rss_feed`; fallback feeds are Bloomberg BR/UK/EU URLs and Yahoo Finance US, while the other collectors use generated Google News, Yahoo Finance, MarketWatch, and Valor URLs. Legacy `rss_feed` mapping can use `NewsItem.asset.market`.
- Correction artifact boundary: `NewsItem` already preserves platform-captured `headline`, optional `summary`, `url`, source label, and timestamps. Capture the immutable verbatim `original_value` from the selected `NewsItem` field in the new correction service; never take it from UI/MCP input or overwrite the artifact.
- Context/recommendation path: `AIService.build_asset_context_pack` selects `NewsItem` records, includes stable `news_item_id`, then ranks through `_source_quality`/`_ranking_score`; this is the one bounded quality extension point. `StrategyValidationService.validate` stores that pack unchanged in `StrategyRecommendation.context_inputs.items`; reverse invalidation can therefore query recommendation JSON context items by `news_item_id` and write a linked invalidation record without rewriting snapshots. `StrategyScenarioFrame` is linked to the same recommendation and its evidence references derive from that stored context.
- Review/API/UI insertion: `StrategyRecommendationSerializer`, `strategy_recommendations` (user-scoped query), `frontend/src/types/index.ts`, `frontend/src/api/ai.ts`, and `TradeNewView.vue` are the existing advisory/review path. Extend this response/type/view with a focused Evidence review section; keep manual submit non-blocking.
- MCP insertion: `mcp.AgentToken` carries the authenticated operator (`user`) and assistant identity (`name`, `origin`, provider/model); existing token-authenticated views scope user-owned portfolio/strategy queries through `agent.user`. Add equivalent evidence operations under `backend/mcp/views.py`/`urls.py`, using the same scoped correction service as UI and persisting the acting `AgentToken` identity in `created_by`. No MCP recommendation/evidence endpoint exists today.

## Open Follow-Ups

- No blocker. The scan found no existing `NewsSource`, correction, artifact-review, source-stance, or recommendation-invalidation model; later tasks must add them without changing existing evidence snapshots. The current MCP asset-insight view also references an undefined `agent` after token lookup; keep this unrelated defect out of this scan-only task unless its task owner elects to fix it.
