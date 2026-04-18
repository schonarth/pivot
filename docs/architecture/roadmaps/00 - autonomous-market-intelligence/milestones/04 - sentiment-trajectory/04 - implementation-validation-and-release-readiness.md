# 04 - Implementation, Validation, and Release Readiness

## Purpose

Integrate deterministic sentiment trajectory into the shared analysis pipeline, validate user-visible trajectory explanations, and confirm Milestone 04 is ready for release.

## Roadmap Milestone

Milestone 04 - Sentiment Trajectory

## Governing ADR

ADR-004 Sentiment Trajectory and Narrative State

## Status

planned

## Owner

unassigned

## Branch

feat/autonomous/04-sentiment-trajectory

## Dependencies

- 00 - milestone coordination.md
- 01 - trajectory-insertion-point-and-signal-source-scan.md
- 02 - deterministic-trajectory-states-and-thresholds.md
- 03 - theme-aggregation-persistence-and-prompt-shape.md

## Required Prior References

- `docs/architecture/adrs/ADR-002-narrative-continuity-for-asset-context.md`
- `docs/architecture/adrs/ADR-003-context-scope-expansion-asset-portfolio-watchlist.md`
- `docs/architecture/adrs/ADR-004-sentiment-trajectory-and-narrative-state.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/02 - temporal-narrative-continuity/03 - prompt-continuity-section-and-ingestion-sentiment.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/03 - portfolio-and-watch-scope/04 - implementation-validation-and-release-readiness.md`

## Likely Files Touched

- backend/ai/*
- backend/markets/*
- backend/mcp/*
- backend/tests/*
- frontend/src/*
- frontend/tests/*
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/04 - sentiment-trajectory/04 - implementation-validation-and-release-readiness.md

## Entry Conditions

- insertion point documented
- deterministic state rules finalized
- theme aggregation, persistence, and prompt shape finalized
- required prior references reviewed

## Background

This is the milestone integration task. Earlier Milestone 04 files define where trajectory belongs, how its state is computed, and what shape it takes. This task applies that design to the shared pipeline and validates that the result improves explanations without changing execution behavior.

## Detailed Requirements

- integrate trajectory into the shared analysis path without creating a parallel reasoning stack
- preserve current asset-analysis behavior when trajectory inputs are absent
- implement asset-scope trajectory first
- apply the same trajectory contract to monitored-set consumers when Milestone 03 outputs are implementation-ready and doing so does not require new monitored-set surface design
- if monitored-set consumers are not implementation-ready, do not block Milestone 04 on them
- compute trajectory on read from retained items and per-item sentiment labels
- do not persist derived trajectory artifacts in Milestone 04
- allow only thin ephemeral non-canonical caching if later profiling shows clear benefit
- do not force a trajectory state when evidence is insufficient or non-directional
- allow user-facing fallback language for weak signal only when it adds explanatory value; otherwise omit the trajectory entry
- validate at least one clear example of each required state:
  - `improving`
  - `deteriorating`
  - `conflicting`
  - `reversal`
- validate at least one price-versus-tone divergence explanation where trajectory helps the final analysis
- keep the milestone inside ADR-004 scope:
  - no trade approval logic
  - no autonomous triggers
  - no long-horizon sentiment history
- if monitored-set consumers are included, reuse the same trajectory contract rather than inventing a separate monitored-set scoring path

## Proposed Approach

- add regression coverage for unchanged asset behavior first
- integrate deterministic trajectory computation at the chosen insertion point
- expose the compact `sentiment_trajectory` section to downstream reasoning
- validate user-visible examples with realistic short-window fixtures
- include monitored-set validation only if Milestone 03 consumers are implementation-ready in the implementation slice

## Validation Scenarios

- current asset analysis still works when no usable trajectory is present
- a recent positive turn after prior negative retained items can be explained as `reversal`
- mixed recent signals with no dominant direction are explained as `conflicting`
- older items outside the retention window do not influence the state
- weak or sparse evidence does not force a canonical state and only surfaces fallback user-facing language when that adds value
- price action divergence can be explained with the added trajectory context
- monitored-set consumers, if implemented, do not drift from asset-level trajectory semantics

## Task Steps

1. Implement deterministic trajectory computation at the selected integration point.
2. Add or update regression coverage for the existing asset path.
3. Add unit tests for all required states and key edge cases.
4. Expose the compact trajectory section to downstream reasoning and affected consumers.
5. Validate representative user-visible examples, including at least one divergence case.
6. Run lint, typecheck, affected unit tests, and milestone integration checks.
7. Prepare UAT notes:
   - user-visible behavior change
   - representative examples
   - known limitations
8. In the final handoff, state explicitly:
   - whether monitored-set consumers were implementation-ready
   - whether trajectory was implemented against them
   - if not, the exact blocking gap
   - whether the roadmap should move directly to Milestone 05 or take a gap-closing detour first

## Tests to Add or Update

- regression tests for existing asset analysis
- deterministic trajectory-state tests
- retention-window tests
- prompt-shape or consumer-shape tests for `sentiment_trajectory`
- monitored-set regression tests if monitored-set consumers are in scope

## Commands to Run

- `cd backend && ruff check .`
- `cd backend && pytest`
- `cd frontend && npm run typecheck`
- run affected frontend tests if frontend code changes
- run milestone integration tests covering trajectory consumers

## Exit Conditions

- required states are implemented deterministically
- trajectory stays bounded to the short window
- analysis output can explain a sentiment shift and at least one price-vs-tone divergence case
- execution behavior is unchanged
- monitored-set readiness and implementation status are reported unambiguously in the final handoff
- tests pass
- release-readiness notes are ready
- task file updated with actual implementation outcome

## Implementation Notes / What Was Done

Not started.

## Open Follow-Ups

- none
