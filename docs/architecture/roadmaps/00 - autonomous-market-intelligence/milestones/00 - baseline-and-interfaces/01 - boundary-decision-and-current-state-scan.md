# 01 - Boundary Decision and Current-State Scan

## Purpose

Document the current system boundaries and define where context selection should stop and reasoning or execution should begin.

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

## Likely Files Touched

- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces/01 - boundary-decision-and-current-state-scan.md
- backend/*
- frontend/*
- docs/reference/prd-mlp.md
- docs/reference/prd-paper-trader.md

## Entry Conditions

- milestone coordination file reviewed
- roadmap reviewed

## Background

Milestone 00 exists to reduce ambiguity before user-facing intelligence work begins. The first baseline need is to understand the system as it already exists and to define where future context-selection work should stop. Without that decision, Milestone 01 risks mixing news gathering, analysis composition, and trading logic in one path.

This task creates the architectural baseline that later milestone tasks can reference instead of repeatedly rediscovering the same seams.

## Detailed Requirements

- identify the current locations of:
  - news ingestion or retrieval
  - technical analysis generation
  - prompt or context assembly
  - analysis generation
  - trade or alert execution
- describe the current flow in concrete system terms, not abstract product language
- define a future-facing separation rule:
  - context selection prepares candidate inputs
  - reasoning interprets those inputs
  - execution acts only on approved outputs
- identify any existing code paths where these responsibilities are currently mixed
- do not propose large refactors in this task
- do not change behavior unless a small protective documentation or interface clarification edit is necessary

## Proposed Approach

- start with a quick repo scan of backend services, MCP- or AI-related code paths, prompt-building utilities, and any current asset analysis flows
- map the flow in the smallest useful form: entrypoint, helpers, outputs, side effects
- capture only the coupling points that matter for later milestones
- if the current code already has useful abstractions, name them explicitly so later tasks reuse them instead of creating parallel paths

## Validation Scenarios

- if a current asset analysis path exists, the scan should be able to point to the exact place where symbol-only context is assembled today
- if news retrieval and prompt assembly already live in different layers, the document should preserve that separation rather than collapsing them conceptually
- if one code path both interprets data and decides actions, that should be named as a coupling risk for later milestones
- a later Milestone 01 task should be able to read this file and identify where context-expansion work belongs without rescanning the entire repo

## Task Steps

1. Scan the project for current news ingestion, technical analysis, prompt building, analysis generation, and trade execution behavior.
2. Identify current seams between data collection, prompt/context assembly, reasoning, and user-visible outputs.
3. Document the current-state architecture in concise form.
4. Define the intended Milestone 00 boundary rule:
   - context selection prepares inputs
   - reasoning interprets inputs
   - execution acts on approved outputs
5. Call out any current coupling that later milestones must avoid reinforcing.
6. Keep recommendations minimal and architectural.

## Current-State Boundary Map

### Current analysis entrypoints

- First-party UI consumer:
  - `frontend/src/views/AssetDetailView.vue`
  - embeds `frontend/src/components/AssetAnalysisTab.vue`
  - calls `GET /api/assets/:id/ai-insight`, `GET /api/assets/:id/ohlcv`, and `GET /api/assets/:id/indicators`
- Agent-facing consumer:
  - `backend/mcp/views.py`
  - `MCPAssetInsightView.post`
  - calls the same `AIService.analyze_asset(asset)` path as the first-party UI

### Current context and reasoning flow

1. Asset-level analysis request enters through `backend/markets/views.py` `AssetViewSet.ai_insight` or `backend/mcp/views.py` `MCPAssetInsightView`.
2. Both entrypoints delegate to `backend/ai/services.py` `AIService.analyze_asset`.
3. `AIService.analyze_asset` currently performs all of the following in one method:
   - verifies AI configuration and budget
   - calculates technical indicators via `trading.technical.IndicatorCalculator.calculate_indicators`
   - refreshes and reads recent news via `markets.services.NewsService.fetch_and_store_news` plus `markets.models.NewsItem`
   - assembles the analysis prompt with `build_indicator_insight_prompt`
   - calls the configured LLM provider
   - parses the model response into the current asset insight shape
   - caches the final analysis artifact for 24 hours
4. The response is returned to UI or MCP consumers with recommendation, confidence, summaries, price target, and selected headlines.

### Current data collection boundaries

- News retrieval and persistence:
  - `backend/markets/services.py` `NewsService`
  - fetches symbol-oriented news from Yahoo Finance, MarketWatch, Valor, and RSS fallback
  - persists results to `backend/markets/models.py` `NewsItem`
- Technical signal generation:
  - `backend/trading/technical.py` `IndicatorCalculator.calculate_indicators`
  - reads persisted `OHLCV`
  - returns a latest-indicator snapshot in memory
  - `IndicatorCalculator.ingest_indicators` can persist a latest snapshot to `TechnicalIndicators`
- Technical chart data for frontend:
  - `backend/markets/views.py` `AssetViewSet.indicators`
  - recalculates full indicator series inline from `OHLCV`
  - does not reuse `IndicatorCalculator`

### Current execution boundaries

- Manual trade execution:
  - `backend/trading/views.py` `TradeViewSet.create`
- Agent-triggered trade execution:
  - `backend/trading/views.py` `agent_execute_trade`
- Alert-triggered execution:
  - `backend/alerts/services.py` `_execute_auto_trade`
- Strategy-triggered execution:
  - `backend/strategies/tasks.py` `evaluate_active_strategies`
  - execution delegated to `StrategyExecutor`

These execution paths consume market data and technical logic, but they do not consume `AIService.analyze_asset` outputs today.

## Milestone 00 Boundary Rule

Future milestones should preserve this separation:

- Context selection:
  - gathers candidate facts, headlines, technical snapshots, and metadata
  - ranks, deduplicates, tags, and bounds those inputs
  - does not interpret what they mean for a trade
- Reasoning:
  - consumes an explicit context pack
  - generates analysis artifacts such as explanations, confidence, scenarios, or recommendations
  - does not place trades, change alerts, or mutate portfolio state
- Execution:
  - consumes explicit approved outputs or deterministic rule inputs
  - applies guardrails and permission checks
  - never infers permission to act from raw context items or free-form analysis text alone

## Current Coupling Risks

- `AIService.analyze_asset` mixes context retrieval, prompt assembly, reasoning, and response shaping in one method. Milestone 01 should avoid extending that coupling further.
- `AssetViewSet.indicators` duplicates technical-calculation responsibility instead of depending on one shared technical-analysis boundary.
- `NewsService.fetch_and_store_news` both fetches and persists in the same step, which is acceptable today but should not become the only interface for future non-asset scopes.
- Strategy and alert execution paths already act on deterministic inputs. Later intelligence milestones should not bypass those paths with free-form LLM output.

## Minimal Architectural Guidance

- Milestone 01 should add richer context selection ahead of `AIService.analyze_asset`, not inside trade or alert execution code.
- New context expansion should reuse current `AssetViewSet.ai_insight` and `MCPAssetInsightView` entrypoints rather than creating a second asset-analysis entrypoint.
- Any future execution-oriented milestone should consume structured analysis outputs, not prompt text.

## Tests to Add or Update

- docs-only baseline task
- no direct unit tests expected unless code is touched to expose or preserve interfaces

## Commands to Run

- if code is touched: run relevant lint, typecheck, and affected tests

## Exit Conditions

- current-state boundary map exists
- intended future separation between context, reasoning, and execution is explicitly documented
- risky existing coupling points are listed
- later milestone tasks can reference this file without re-scanning the full codebase from scratch

## Implementation Notes / What Was Done

Reviewed the roadmap and execution model, then scanned the live asset-analysis and execution paths in backend and frontend. Documented the current entrypoints, identified `AIService.analyze_asset` as the present coupling hotspot, and recorded the separation rule Milestone 01 should preserve.

## Open Follow-Ups

- decide whether any existing code needs protective refactoring before Milestone 01
