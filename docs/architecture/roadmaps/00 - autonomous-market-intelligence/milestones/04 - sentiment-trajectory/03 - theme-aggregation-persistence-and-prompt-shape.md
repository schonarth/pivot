# 03 - Theme Aggregation, Persistence, and Prompt Shape

## Purpose

Define when theme-level trajectory is allowed, whether short-window derived trajectory should be persisted, and how the trajectory section enters downstream reasoning without bloating prompts.

## Roadmap Milestone

Milestone 04 - Sentiment Trajectory

## Governing SPEC

SPEC-004 Sentiment Trajectory and Narrative State

## Status

done

## Owner

GPT-5.4 / implementation

## Branch

feat/autonomous/04-sentiment-trajectory

## Dependencies

- 00 - milestone coordination.md
- 01 - trajectory-insertion-point-and-signal-source-scan.md
- 02 - deterministic-trajectory-states-and-thresholds.md

## Required Prior References

- `docs/specs/SPEC-003-context-scope-expansion-asset-portfolio-watchlist.md`
- `docs/specs/SPEC-004-sentiment-trajectory-and-narrative-state.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/01 - asset-context-expansion/03 - deduplication-ranking-and-context-pack-shape.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/02 - temporal-narrative-continuity/03 - prompt-continuity-section-and-ingestion-sentiment.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/03 - portfolio-and-watch-scope/03 - clustering-prioritization-and-composition.md`

## Likely Files Touched

- backend/ai/*
- backend/mcp/*
- backend/tests/*
- frontend/src/*
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/04 - sentiment-trajectory/03 - theme-aggregation-persistence-and-prompt-shape.md

## Entry Conditions

- deterministic state rules defined
- insertion point documented
- SPEC-004 prompt and persistence boundaries reviewed

## Background

SPEC-004 now fixes the milestone-level policy for theme aggregation, compute-on-read trajectory, and weak-signal handling. This task turns those decisions into an exact implementation contract for prompt shape and optional optimization boundaries before integration begins.

## Detailed Requirements

- define the minimum auditable condition for theme-level aggregation
- define when the system must stay asset-level only
- define the compute-on-read trajectory model and optional optimization boundary
- define the compact output shape for downstream reasoning input
- define how trajectory entries interact with monitored-set composition if Milestone 03 outputs exist
- keep the output small enough for asset and monitored-set prompts without timeline dump behavior
- keep model-generated prose out of the canonical stored record

## Proposed Approach

- prefer asset-level trajectory as the baseline
- allow theme-level entries only when theme identity is explicit, stable, traceable back to retained items, and shared across more than one asset
- compute trajectory on read from retained items and per-item sentiment labels
- do not persist derived trajectory artifacts in Milestone 04
- allow only thin ephemeral non-canonical caching if profiling later shows repeated recomputation on the same request path
- define one compact `sentiment_trajectory` shape reusable by asset and monitored-set consumers

## Validation Scenarios

- weak or inferred theme linkage does not produce a theme-level trajectory
- a single-asset topic does not produce a theme-level trajectory even when that asset has several retained items with the same theme tag
- asset-level trajectory still emits when theme linkage is unavailable
- prompt shape stays compact for one asset and for a monitored set with multiple implicated assets
- any optimization cache remains optional, ephemeral, and non-canonical

## Task Steps

1. Define the auditable rule for theme-level aggregation.
2. Define the canonical compute-on-read trajectory model and optional optimization boundary.
3. Define the downstream `sentiment_trajectory` shape.
4. Define how asset and monitored-set consumers reuse the same shape.
5. Identify prompt-budget and optimization regression tests needed for implementation.

## Tests to Add or Update

- unit tests for theme-aggregation eligibility
- prompt-shape or serializer tests for `sentiment_trajectory`
- tests for compute-on-read correctness and optional cache transparency if any cache is added

## Commands to Run

- `cd backend && ruff check .`
- run affected backend tests around trajectory aggregation and prompt shaping
- `cd frontend && npm run typecheck` if frontend consumers change

## Exit Conditions

- theme-aggregation rule explicit
- compute-on-read boundary explicit
- prompt shape explicit
- consumer reuse path explicit

## Implementation Notes / What Was Done

Completed theme aggregation and prompt-shape wiring.

What was done:

- kept asset-level trajectory as the baseline and allowed theme-level entries only for explicit normalized theme tags
- required cross-asset evidence before emitting theme trajectory
- kept derived trajectory compute-on-read and out of persistent storage
- added a compact `sentiment_trajectory` shape to asset and monitored-set analysis output
- reused the same prompt section for both asset and monitored-set analysis paths

## Open Follow-Ups

- none
