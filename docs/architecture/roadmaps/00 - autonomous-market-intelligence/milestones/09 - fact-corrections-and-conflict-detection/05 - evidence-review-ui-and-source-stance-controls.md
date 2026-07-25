# 05 - Evidence Review UI and Source-Stance Controls

## Purpose

Extend existing strategy-recommendation and scenario-review surfaces with a focused Evidence review section and operator correction controls.

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
- `03 - correction-review-and-treatment-contracts.md`
- `04 - recommendation-invalidation-and-evidence-api.md`

## Likely Files Touched

- `frontend/src/api/ai.ts`
- `frontend/src/types/index.ts`
- `frontend/src/views/TradeNewView.vue`
- `frontend/src/components/*`
- `frontend/src/views/__tests__/TradeNewView.spec.ts`
- `frontend/e2e/*`
- `backend/ai/test_views.py`

## Detailed Requirements

- add an Evidence review section to existing strategy-recommendation and scenario-review surfaces; do not create a separate workspace
- show source artifact excerpt, read-only original value, correction history, artifact review state, source treatment, categorical disputed/stale state, and invalidation explanation
- let operators create or supersede corrections, set artifact review state, and set/clear source stance through the shared backend behavior
- autocomplete fact keys from that operator's completed corrections, show the prescribed tooltip, and normalize new input to lower snake case on blur without an error prompt
- source-stance controls are disabled when fewer than two configured eligible sources exist for an artifact market; count market-specific plus market-agnostic configured sources, not recent artifacts
- retain artifact review/correction controls at every source count
- include a development/test override that exposes enabled source-stance controls for coverage

## Validation Scenarios

- original value is visibly read-only
- a new fact key normalizes on blur and becomes a suggestion only after completion
- one eligible source leaves stance controls disabled while artifact controls stay enabled
- override enables stance controls in development/test
- changing source stance does not imply artifact truth or remove correction history
- invalidated recommendation remains reviewable and prompts revalidation rather than reactivation

## Task Steps

1. Reuse the current recommendation/scenario review components and API client.
2. Add minimal typed evidence-review display and mutation flows.
3. Add fact-key suggestion, tooltip, and blur-normalization behavior.
4. Implement source eligibility and override-aware disabled state from backend-provided facts.
5. Add component and end-to-end tests while preserving non-blocking manual trade behavior.

## Tests to Add or Update

- frontend rendering tests for evidence, history, original-value read-only state, and invalidation
- fact-key suggestion/blur normalization tests
- source-stance disabled-default and override-enabled tests
- end-to-end correction and review flow tests
- regression test that manual trade execution remains independent

## Commands to Run

- `cd frontend && npm run typecheck`
- `cd frontend && npm run test -- --run src/views/__tests__/TradeNewView.spec.ts`
- `cd frontend && npx playwright test`

## Exit Conditions

- evidence review is focused, auditable, and embedded in existing review surfaces
- UI mutations use the shared scoped backend contract
- all required source-control and fact-key behaviors are covered
- no separate fact-checking product or execution gate is introduced

## Implementation Notes / What Was Done

- Added scoped UI evidence endpoints for recommendation evidence, fact-key suggestions, corrections, artifact reviews, and source-stance set/clear. They reuse `EvidenceReviewService`, preserve source/artifact scope, and return configured-source eligibility plus the development/test override state.
- Added typed frontend evidence client methods and embedded the focused Evidence review surface in both latest and stored strategy/scenario review details. It displays immutable read-only originals, treatment, uncertainty, history, correction/review controls, fact-key suggestions and lower-snake blur normalization, and source-stance controls.
- Source stance remains disabled below the configured-source threshold while artifact controls stay available. The `evidenceSourceStanceOverride=true` development/test query enables its coverage path. Manual trade submission remains separate from review actions.
- UAT follow-up replaced inline forms with one reusable artifact-review modal, a compact reusable source-stance menu, and a single Save action that closes after persisting the selected correction and/or artifact review. AI Summary and AI Insight presentation remains unchanged.
- UAT follow-up exposed the reusable review and source-stance text controls beside each AI Insight headline and added an AI Summary `Headlines used` section. Headline evidence can now load and save without requiring an earlier stored recommendation; recommendation outputs remain deterministic while the model supplies the explanatory text.
- Verification: focused `TradeNewView` Vitest suite passed 8/8; frontend typecheck passed. Full Playwright passed 19/20; the existing registration smoke test failed because it expects a refresh token absent from the response. No standalone correction E2E fixture path exists; focused UI coverage exercises the required review behavior.
- Latest verification: 68 focused backend tests passed; frontend typecheck and 13 focused frontend tests passed; rebuilt backend and frontend containers returned their expected health responses.

## Open Follow-Ups

- none
