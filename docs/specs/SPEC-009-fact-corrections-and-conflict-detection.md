---
name: Fact Corrections and Conflict Detection
description: Spec for correction safety and conflict visibility before autonomous paper-trading execution
type: reference
---

# SPEC

## SPEC-009 Fact Corrections and Conflict Detection

Status: Approved

## Roadmap Position

This SPEC corresponds to Milestone 9 of the Autonomous Market Intelligence roadmap:

- [Autonomous Market Intelligence Roadmap](../roadmaps/00%20-%20autonomous-market-intelligence/roadmap.md)

Its role is narrow: detect important factual conflicts, allow operator corrections without erasing history, and surface unstable facts before any autonomous execution is enabled.

It is not intended to execute trades, train self-improving strategies, or replace the existing context-building and strategy-validation pipeline.

## Context

SPEC-001 through SPEC-006 build market context, narrative continuity, sentiment trajectory, divergence reasoning, and discovery. SPEC-007 turns explicit trade ideas into paper-only validation records. SPEC-008 adds bounded scenario and risk framing to those strategy recommendations.

That still leaves a safety gap: the system can preserve and reuse analysis evidence, but it does not yet have a structured way to flag stale, contradicted, or operator-corrected facts before a later autonomous layer relies on them.

Before autonomous paper trading can be enabled, operators need to see when key inputs are unstable, corrected, or disputed. The system should preserve the original evidence while making correction state visible to analysis, scenario framing, and future execution gating.

## Decision

Milestone 9 should add a correction and conflict-detection layer around important analysis facts.

That layer should:

1. identify factual conflicts in selected context and stored recommendation evidence
2. allow manual correction records without mutating or deleting the original evidence
3. expose correction state in the existing strategy-recommendation and scenario-review surfaces
4. make unstable facts available as explicit inputs to later autonomous gating
5. keep correction authority operator-visible and auditable

Corrections should affect interpretation, not history. The original headline, context item, recommendation input, or scenario evidence should remain available for audit.

The first consumers should be:

1. strategy recommendation review
2. scenario framing review
3. future autonomous execution gating

## Intended Shape

The future implementation should treat corrections as linked records attached to existing analysis artifacts, not as silent rewrites of source context.

Expected flow:

1. collect selected context and stored recommendation evidence
2. receive a candidate conflict raised by an operator or delegated MCP assistant and validate its structured fields deterministically
3. show each cited artifact, its review state, and its correction history in an Evidence review section of the existing strategy-recommendation and scenario-review surfaces
4. allow an operator, through the UI or a delegated MCP assistant, to correct a fact, set an artifact review state, or set a bounded source stance
5. persist those records linked to the affected evidence
6. apply the resulting fact and weight treatment deterministically in strategy recommendation and scenario review output, and invalidate affected stored recommendations
7. make future autonomous execution check correction state before paper trade execution

The Evidence review section should be a focused extension of existing review surfaces, not a separate fact-checking workspace. It should show the original artifact excerpt, linked correction history, and the current artifact and source treatment before an operator records a change.

The `fact_key` field should autocomplete unique keys from completed correction records in the current operator's scope. It should include an information tooltip: "Describe it in one ample term such as `corporate_action` or `earnings_result`." An operator may select a suggestion or enter a new key. On blur, new input must be normalized to lower snake case without prompting or presenting a validation error. A key is persisted only when its correction record is completed; abandoned work contributes no suggestion.

Each correction must retain a platform-provided, verbatim `original_value` from the selected source artifact. It is immutable after capture. The fact contestation UI must display it as read-only, and MCP may reference the source artifact but may not supply or alter the value independently.

MCP must provide the equivalent evidence-review and correction operations for an authenticated operator's assistant. The assistant may retrieve evidence and correction history, including the operator's unique existing `fact_key` values, then create or supersede fact corrections, artifact review states, and source stances within the operator's authorized scope. MCP guidance should prefer an existing key when suitable and permit a new key otherwise. UI and MCP operations must use the same backend behavior and deterministic treatment rules. Each MCP action must retain the authenticated assistant identity in `created_by` for audit.

Artifacts are valid inputs by default and do not require operator confirmation. Artifact and source treatment adjusts only the existing context-selection source-quality dimension: accepted or trusted adds `+1`; disputed, stale, or untrusted subtracts `-1`; the effective quality is clamped to `0..4`. An artifact-level adjustment overrides a source-level adjustment for that artifact. This numeric treatment may affect which artifacts are selected into bounded context, but does not numerically alter a strategy verdict, scenario confidence band, or autonomous-execution decision.

A source is a small system-managed `NewsSource` record with an institution name, feed URL, and optional market. Each news artifact must link to its actual source rather than a generic acquisition label such as `rss_feed`. No source onboarding or management surface is required in this milestone.

The implementation must migrate existing source data before relying on `NewsSource`. It must seed records for the current feed URLs, map legacy `rss_feed` artifacts by the linked asset's market to the corresponding Bloomberg or Yahoo Finance feed record, and map other known source labels to their canonical records. New ingestion must link each artifact directly to its `NewsSource`. Legacy source text may remain only as historical provenance, never as the active source identity.

An operator may set a source-wide stance for a `NewsSource` within their own evidence scope. A trusted source receives the positive context-selection adjustment across that operator's artifacts; an untrusted source receives the negative adjustment. Neither stance makes every artifact true or invalid. A fact correction overrides the original fact for downstream interpretation. Disputed and stale facts remain explicit categorical uncertainty signals for strategy and scenario review regardless of their context-selection adjustment.

An operator may clear an active source stance to restore default source quality. Clearing a stance closes the active record by recording when and by whom it was superseded; it does not delete history or create an active neutral stance. Marking a new stance follows the same record lifecycle.

For an artifact's market, eligible sources are configured `NewsSource` records assigned to that market plus market-agnostic records with no market assignment. Source-stance controls remain disabled when zero or one eligible source exists. The count must use configured sources, not merely sources that recently produced artifacts. Artifact-level review and correction controls remain available regardless. A development/test override must expose source-stance controls so their enabled behavior receives UI and end-to-end coverage.

AI may extract candidate facts or explain downstream impact within an operator- or assistant-initiated review. It must not generate a conflict queue or silently set correction records, artifact review states, or source stances. Applying those records and their weight adjustments must remain deterministic.

Material fact corrections and artifact `disputed` or `stale` states must invalidate every stored recommendation in the same operator scope whose stored context includes the affected artifact. Source stance changes affect future context selection only and do not retroactively invalidate recommendations.

Invalidation must use a reverse `RecommendationInvalidation` record linked to both the recommendation and the triggering correction or artifact-state record. Recommendation queries determine `is_invalidated` by checking for related invalidations and may preload the newest record for explanation. An invalidated recommendation remains immutable and auditable; revisiting it creates a fresh recommendation through the existing validation path. A later correction never silently reactivates an invalidated recommendation.

Recommended minimum structured fields:

- `source_artifact_type`
- `source_artifact_id`
- `source_id`
- `fact_key`
- `original_value`
- `corrected_value`
- `correction_state`
- `artifact_review_state`
- `source_stance`
- `reason`
- `created_by`
- `created_at`
- `superseded_at`

Recommended minimum source fields:

- `institution_name`
- `feed_url`
- `market` (optional)

Recommended minimum source-stance fields:

- `source_id`
- `operator_id`
- `stance`
- `created_by`
- `created_at`
- `superseded_at`
- `superseded_by`

Recommended minimum recommendation-invalidation fields:

- `recommendation_id`
- `trigger_record_id`
- `trigger_type`
- `created_at`

Allowed `correction_state` values should stay small. A first implementation may use:

- `corrected`
- `disputed`
- `stale`

Artifact review state may use `accepted`, `disputed`, or `stale`. Source stance may use `trusted` or `untrusted`.

## Resolved Decisions

- Corrections are reviewed within existing strategy-recommendation and scenario-review surfaces through a focused Evidence review section; no separate fact-checking workspace is required.
- Artifacts remain usable by default. Operator acceptance increases bounded evidence weight; it does not make an artifact valid only after acceptance.
- Source-wide treatment is a bounded weighting adjustment, not a truth or validity decision for every artifact.
- Milestone 09 applies numeric treatment only to the existing context-selection source-quality dimension: `+1` for accepted or trusted, `-1` for disputed, stale, or untrusted, clamped to `0..4`. Strategy verdicts, scenario confidence, and autonomous decisions remain categorical.
- Sources are system-managed records with an institution name, feed URL, and optional market; every artifact links to its actual source, never a generic `rss_feed` bucket.
- Existing source data is migrated to seeded `NewsSource` records. Legacy `rss_feed` artifacts map deterministically through their linked asset market; new ingestion writes the canonical source relationship directly.
- Source stances are per operator. Source-wide controls are available only when at least two configured `NewsSource` records are eligible for the artifact's market, including market-agnostic sources; artifact-level review remains available at all source counts. A development/test override covers the enabled state.
- Clearing trusted or untrusted source stance restores default quality by superseding the active stance record. Every mark, replacement, and clear remains auditable without a separate history model.
- Fact keys are operator-local suggestions derived only from completed correction records. UI input normalizes new keys to lower snake case on blur; MCP receives the same suggestions and may provide a new key when needed.
- Each correction retains an immutable, platform-provided verbatim `original_value` from its selected source artifact. The fact contestation UI displays that value read-only, and MCP cannot supply or alter it independently.
- Material fact and artifact corrections create reverse `RecommendationInvalidation` records for affected stored recommendations. Query-time existence determines whether a recommendation is invalidated; invalidation is permanent and requires revalidation rather than reactivation.
- Source stance changes affect future context selection only; they do not invalidate existing recommendations.
- Precedence is: fact correction, then artifact review state, then source stance, then baseline treatment.
- Operators or delegated MCP assistants initiate candidate conflicts. AI may assist within that review but does not generate a conflict queue; operators create or change correction, artifact-review, and source-stance records. Deterministic rules apply their effects.
- An operator may delegate evidence verification and correction to an authenticated MCP assistant; MCP and UI use the same scoped operations and audit rules.

## Constraints

- Corrections must preserve original evidence and audit history.
- Correction state must be structured before it is rendered as prose.
- Manual correction workflow must be operator-visible.
- Strategy validation and scenario framing must not silently ignore disputed or stale facts.
- Future autonomous execution must be able to read correction state without parsing free-form notes.
- Artifact and source treatment must use bounded deterministic adjustments, not validity gates.
- No shared numeric confidence or evidence score for strategy verdicts, scenario confidence, or autonomous decisions is introduced in this milestone.
- MCP correction operations must enforce the existing authenticated operator scope and retain the acting assistant identity in audit history.
- `original_value` must come from the selected source artifact and remain immutable after capture.
- Source-stance behavior must have unit coverage and end-to-end coverage for both the disabled default and override-enabled UI states.
- Source-stance audit history must preserve marking, replacement, and clearing actions.
- Source migration must preserve every existing artifact and give it a canonical `NewsSource` identity before source stance is used.
- Recommendation queries must expose invalidation state without mutating historical recommendation snapshots.

## Non-Goals

- No autonomous trade execution.
- No automatic mutation or deletion of historical context.
- No self-improving strategy behavior.
- No broad fact-checking product outside the market-intelligence pipeline.
- No AI-generated conflict queue.
- No initial fact-key catalog or fact-key management surface.
- No source onboarding, source-management controls, or universal trust-scoring system.
- No new scoring taxonomy unless required by correction-state review.

## Validation

- unit coverage for source identity, legacy source migration, per-operator stance isolation, mark/clear audit history, deterministic precedence, bounded context-selection adjustments, and recommendation invalidation
- end-to-end coverage for dormant source-stance controls, the development/test override that enables them, and fact-key suggestion and normalization behavior

## Notes

This SPEC should remain independently mergeable when implemented. It is a mergeable foundation for Milestone 10 rather than a standalone user release.

Expected user-facing value:
- Operators can see and correct unstable facts before the system uses them for autonomous paper-trading decisions.
