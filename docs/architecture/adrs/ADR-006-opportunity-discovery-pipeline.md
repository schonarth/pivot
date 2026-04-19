---
name: Opportunity Discovery Pipeline
description: Draft ADR for bounded asset discovery using deterministic preselection and on-demand refinement
type: reference
---

# ADR

## ADR-006 Opportunity Discovery Pipeline

Status: Approved

## Roadmap Position

This ADR corresponds to Milestone 6 of the Autonomous Market Intelligence roadmap:

- [Autonomous Market Intelligence Roadmap](../roadmaps/00%20-%20autonomous-market-intelligence/roadmap.md)

Its role is narrow: find assets worth watching before they are held by producing a bounded, auditable shortlist from a larger eligible universe.

It is not intended to authorize buying, replace strategy validation, or perform mandatory full-market AI scans.

## Context

ADR-001 expands asset context. ADR-002 adds bounded continuity. ADR-003 generalizes analysis to monitored sets. ADR-004 adds short-window sentiment trajectory. ADR-005 explains expected-vs-actual divergence.

That still leaves a product gap: the current intelligence path is strongest once a user already holds or explicitly watches an asset.

Users eventually need answers such as:

- what new assets are worth watching today
- which names passed a disciplined first-pass screen instead of surfacing from noise
- why one candidate ranks ahead of another
- how a surfaced candidate becomes part of ongoing watch monitoring without manual re-entry

Without a bounded discovery layer, the system can analyze known assets well, but it cannot proactively surface a small set of new candidates worth attention.

## Decision

Milestone 6 should add a bounded opportunity-discovery pipeline with two explicit stages:

1. deterministic universe selection and technical pre-filtering
2. bounded ranking and optional refinement for the survivors

The pipeline should produce a capped shortlist of assets to watch, not an unconstrained scan report.

Each surfaced asset should include:

- a compact ranking record
- concise technical rationale
- concise context rationale when available
- enough traceability to explain why it surfaced

The first consumer should be:

1. scheduled preselection output for users
2. user-initiated candidate refinement when the user opens discovery and deeper explanation is available

Future milestones may reuse discovery outputs later for:

1. watch-scope population
2. strategy validation candidate intake

Discovery should remain separate from execution. A surfaced candidate is only a watch candidate unless a later milestone explicitly validates and approves a trade idea.

## Intended Shape

The future implementation should treat discovery as a bounded pipeline layered on top of the existing intelligence system, not as a separate autonomous agent.

Expected flow:

1. define one explicit eligible universe
2. run deterministic technical pre-filters across that universe
3. cap the survivors to a manageable candidate set
4. build deterministic non-LLM candidate records for those survivors
5. emit a capped preselected "assets to watch" output
6. optionally refine surfaced candidates when the user actively opens discovery and LLM access is available
7. allow explicit handoff from discovery output into watch scope

The discovery output should stay compact and reviewable. It should not require generating large narrative reports for every scanned asset.

## Resolved Decisions

### Eligible Universe Must Be Explicit

Milestone 6 should operate on an explicit eligible universe, not on an implicit "entire market" concept.

Approved first implementation:

- all assets in one explicit market at a time

Meaning:

- the discovery run is market-scoped
- the eligible universe starts from the current stored asset set for that market
- assets already held in any of the user's portfolios are excluded before discovery filtering begins
- as new assets are added to the product, they automatically become eligible for that market's discovery runs

Allowed future variants:

- one configured market universe
- one user-selected exchange inside a market
- one curated tradable asset set already present in project data

Not approved in this milestone:

- hidden or changing universe boundaries
- mandatory all-market crawling before every run
- unbounded source expansion during discovery itself

Reason:

- discovery needs auditable denominator control
- performance and cost stay predictable
- ranking quality is easier to interpret when the input set is explicit
- the current seeded asset base is small enough that per-market scanning remains comfortably bounded
- discovery should surface new watch candidates rather than re-suggest assets the user already holds

### Technical Pre-Filter Comes Before Context Expansion

Milestone 6 should require a deterministic technical pre-filter before context-aware ranking.

Meaning:

- the larger universe is reduced first using bounded, explainable technical criteria
- context-building cost is reserved for the surviving candidates
- the system should not perform the most expensive reasoning across the whole eligible universe

This milestone favors disciplined narrowing over exhaustive intelligence on every asset.

### Prefilter Criteria Should Stay Small and Deterministic

Milestone 6 should use a small initial filter set that is explainable and easy to tune.

Approved first implementation:

- liquidity floor
- trend intact
- breakout or near-breakout confirmation

Recommended shape:

- minimum liquidity threshold
- short trend above long trend
- close above, or within a small configurable distance of, a recent high or breakout level

This gives the scheduled pre-filter an assertive point of view before the user asks for deeper refinement. It favors "worth watching now" candidates over a looser list of merely active names.

Options considered:

- `liquidity + momentum`
  - simplest
  - rejected as the first default because it risks surfacing names that are already obviously extended without enough structure for a watchlist-oriented shortlist
- `liquidity + breakout`
  - eventful and easy to explain
  - rejected as the first default because raw breakout logic is noisier without trend confirmation
- `liquidity + trend`
  - stable and interpretable
  - rejected as the first default because it can be too slow and may not say enough about immediate watch-worthiness
- `liquidity + momentum + volatility expansion`
  - strong "why now" signal
  - rejected as the first default because it adds tuning complexity too early
- `small additive score`
  - flexible
  - rejected as the first default because it drifts toward a more complex scoring system before the simplest assertive scheduled screen is proven

Why this option was chosen:

- it better matches the product goal of surfacing assets worth watching, not just assets already moving
- it balances timeliness and quality better than a raw momentum or raw breakout screen
- it stays deterministic and explainable while being more thorough than the smallest two-rule alternatives

Examples of other acceptable first-pass filters:

- minimum liquidity or activity threshold
- recent price-move or volatility threshold
- trend or breakout-style indicator threshold
- relative-strength or momentum-style threshold

Future direction:

- if discovery proves valuable, later iterations may allow user-selectable prefilter profiles
- Milestone 6 should still ship with one assertive default recipe rather than asking users to configure the scheduled screen up front

Not approved in this milestone:

- opaque learned ranking models
- broad heuristic sprawl with many overlapping weights
- LLM-only first-pass filtering

### Candidate Cap Is Required

Milestone 6 should cap the number of candidates at two points:

1. after technical pre-filtering
2. in the final surfaced shortlist

Reason:

- context cost must remain bounded
- user review must stay practical
- discovery should optimize for attention, not exhaustiveness

The exact caps may be configuration values, but the milestone requires explicit caps rather than open-ended result counts.

Approved first implementation:

- pre-filter survivor cap: `20`
- final surfaced shortlist cap: `5`

Why this cap was chosen:

- it gives the deterministic screen enough room to be selective without becoming brittle
- it keeps the final user-facing output sharp and reviewable
- it preserves a sense of daily novelty; a larger first-pass shortlist would risk making discovery feel exhausting or stale too quickly

Options considered:

- tighter cap such as `10 -> 5`
  - more opinionated
  - rejected as the first default because it may become too brittle on quieter days
- broader cap such as `20 -> 10`
  - broader exploration
  - rejected as the first default because it increases user fatigue and weakens the sense of a curated daily shortlist
- much looser cap such as `50 -> 5`
  - leaves more room for downstream ranking
  - rejected as the first default because it adds breadth without a matching need at this milestone
- market-relative caps
  - scale with universe size
  - rejected as the first default because fixed caps are easier to reason about while the asset universe remains comfortably bounded

### Scheduled Runs Must Stay Non-LLM

Milestone 6 should allow scheduled discovery only for deterministic preselection.

Meaning:

- scheduled runs may select and rank candidates using deterministic inputs
- scheduled runs should not automatically trigger LLM refinement
- token-consuming refinement should happen only after explicit user initiation

Reason:

- LLM usage has direct cost
- users should control when deeper refinement is worth the spend
- the baseline discovery loop should remain cheap and predictable

This milestone should treat LLM refinement as an optional second step, not as a requirement for every scheduled run.

### Refinement Should Be User-Initiated

Milestone 6 may support LLM-assisted refinement for already preselected candidates, but only on demand after the user actively opens the discovery surface.

Allowed:

- refine surfaced candidates after the user opens discovery and LLM access is available
- refine the surfaced shortlist in one user-initiated pass rather than requiring per-candidate clicks
- cache refined results for later reuse until the underlying discovery output changes or expires

Not approved in this milestone:

- automatic LLM refinement of every surfaced candidate
- background refinement triggered only because a schedule fired
- LLM-first ranking over the full eligible universe

Meaning:

- opening the discovery experience is the explicit user action that authorizes token spend
- the system does not spend tokens for users who never open the feature
- when a user does open the feature, refining the surfaced shortlist is acceptable because it improves the immediately viewed result set
- cached refined output is an optimization and should not change the deterministic preselected shortlist itself

### Ranking Should Be Context-Aware But Bounded

Milestone 6 should rank surviving candidates using bounded, auditable signals after pre-filtering.

Approved first implementation:

- use a small blended deterministic score
- combine technical setup quality with bounded context support

Expected ranking inputs may include:

- technical posture from the pre-filter stage
- deterministic context metadata derived from ADR-001
- continuity cues from ADR-002 when available
- sentiment trajectory from ADR-004 when available
- divergence evidence from ADR-005 when it materially strengthens or weakens the opportunity case

Recommended first-pass ranking dimensions:

- technical setup quality
- breakout proximity or confirmation quality
- context support
- freshness

Why this option was chosen:

- it better matches the product goal of surfacing assets worth watching now, not only the technically strongest charts in isolation
- it stays deterministic while producing a more balanced and assertive shortlist
- it gives bounded context meaningful influence without requiring LLM generation or a large scoring system

Options considered:

- pure technical priority
  - simplest
  - rejected as the first default because it underweights narrative and timing support
- technical first, context as tie-breaker
  - safer and more chart-led
  - rejected as the first default because context would have too little influence on the final shortlist
- bucketed ranking
  - interpretable
  - rejected as the first default because it adds extra rule surface without clear gain over a small blended score
- freshness-forward ranking
  - strong daily novelty
  - rejected as the first default because it risks overvaluing recency over setup quality
- user-selectable ranking modes
  - flexible
  - rejected for Milestone 6 because scheduled discovery should ship with one assertive point of view before adding user-facing configuration

Guardrails:

- keep the blended score small and documented
- avoid many overlapping sub-weights
- prefer interpretable dimensions over fine-grained pseudo-precision

The ranking layer should remain bounded and auditable. It should prefer small structured inputs over broad free-form reasoning.

Meaning:

- the system may explain why a candidate is timely
- the scheduled baseline should work without LLM generation
- the system should not invent a fully autonomous thesis engine here
- later strategy validation still owns approve, reject, or defer decisions

### Output Shape Must Be Structured First

Milestone 6 should emit structured discovery records first, with optional small display text layered on top.

Recommended minimum fields:

- `asset_id`
- `symbol`
- `market`
- `rank`
- `technical_signals`
- `context_summary`
- `discovery_reason`
- `watch_action_ready`

Meaning:

- `technical_signals`: compact structured evidence for why the asset survived the pre-filter
- `context_summary`: bounded context cues that affect watch-worthiness; this may be deterministic metadata when LLM refinement has not been requested
- `discovery_reason`: concise surfaced rationale suitable for UI display; this should have a deterministic fallback form when LLM refinement is unavailable or not requested
- `watch_action_ready`: indicates the candidate can be added to watch scope without re-derivation

User-facing prose may summarize the result, but prose should not become the canonical discovery record.

### Non-LLM Fallback Is Required

Milestone 6 should remain useful when LLM refinement is unavailable, disabled, or not requested.

Approved first implementation:

- structured discovery record remains the canonical fallback output
- each surfaced candidate also includes one short deterministic one-line explanation assembled from structured inputs

Minimum expectation:

- the system still returns a capped shortlist
- each candidate still includes structured technical evidence
- each candidate still includes a compact deterministic reason assembled from stored inputs

Recommended fallback shape:

- canonical structured fields such as rank, technical signals, context summary, and freshness indicators
- one concise deterministic sentence summarizing why the asset surfaced
- optional compact badges beneath that summary when the UI benefits from them

Why this option was chosen:

- it preserves auditability because the structured record remains primary
- it gives users a readable explanation without spending LLM tokens
- it is substantially more usable than a badge-only or score-only fallback while staying bounded and repeatable

Options considered:

- purely structured output
  - safest and most auditable
  - rejected as the first default because it asks users to assemble the story themselves
- structured output plus templated bullets
  - expressive and readable
  - rejected as the first default because it adds more UI and copy surface than needed for a bounded fallback
- headline-style labels plus structure
  - strong browsing feel
  - rejected as the first default because it introduces a label taxonomy too early
- score explanation only
  - transparent
  - rejected as the first default because component scores alone do not explain enough and can imply false precision

The fallback output may be less expressive than refined output, but it should still be sufficient for users to decide whether to inspect or watch the asset.

This milestone should fail soft, not fail closed, when model access is unavailable.

### Watchlist Handoff Should Be Explicit

Milestone 6 should allow discovery output to populate watch scope without manual duplication.

Meaning:

- discovery should emit enough stable identity and metadata for a watch insertion action
- the watch addition should be explicit and user-visible
- discovery should not silently mutate watch membership as a side effect of scanning

This keeps Milestone 6 aligned with ADR-003, where watch membership remains explicit and deterministic.

### Scheduling Is Allowed, Autonomy Is Not

Milestone 6 should support scheduled or daily deterministic preselection output as a delivery mode.

Allowed:

- on-demand run
- scheduled daily run
- bounded recurring scan over the explicit universe
- user-initiated refinement of surfaced candidates when discovery is opened

Not approved in this milestone:

- autonomous buy behavior
- self-escalating scan frequency based on model confidence
- scheduled LLM refinement
- hidden background actions that change user portfolios

Scheduling is a presentation and delivery concern. It does not grant execution authority.

### Persistence Boundary

Milestone 6 may persist enough data to support reviewability and watch handoff, but it should avoid creating a heavy new historical warehouse by default.

Reasonable persistence for this milestone may include:

- last surfaced discovery records
- lightweight ranking metadata
- linkage from surfaced candidates to explicit watch additions

Not approved in this milestone:

- unbounded storage of every scanned asset result for every run
- model-generated narrative blobs as the canonical store
- direct execution instructions derived from discovery outputs

Thin ephemeral caching is allowed when it remains a pure optimization layer and can be dropped without affecting correctness.

Allowed refinement caching for this milestone:

- cache user-triggered refined shortlist output
- reuse cached refined output while the underlying deterministic shortlist remains current
- invalidate or refresh cached refinement when the shortlist changes materially, expires, or the user requests a fresh refinement

Approved first implementation:

- keep only the latest refined shortlist cache
- bind that cache to the deterministic shortlist fingerprint
- apply a hard cache TTL of `24h`

Invalidate cached refinement when:

- shortlist membership changes
- shortlist ordering changes materially
- the cache reaches its TTL
- the user explicitly requests refresh
- refinement-relevant model or prompt configuration changes

Why this option was chosen:

- it minimizes repeated token spend for users who revisit the same shortlist
- it stays logically tied to the exact deterministic shortlist that produced the refined output
- it avoids turning cache into a broader discovery-history feature too early

Options considered:

- latest-only cache with TTL only
  - simple
  - rejected as the first default because it can reuse refinement even when the shortlist changed
- latest-only cache tied only to shortlist fingerprint
  - logically clean
  - rejected as the first default because a hard max age still provides a useful freshness boundary
- short history of refined shortlists
  - stronger audit trail
  - rejected for Milestone 6 because it turns cache into a larger product feature
- session-only cache
  - cheapest
  - rejected because it does not deliver enough value for returning users

### Reviewability and Validation

Milestone 6 should be validated in two layers:

1. deterministic fixture-style validation for filter and ranking behavior
2. a human-review surface for checking why assets surfaced

Validation should confirm:

- the eligible universe is explicit
- pre-filter rules are reproducible
- shortlist caps are respected
- deterministic fallback reasons are concise and grounded in stored inputs
- optional refinement is only triggered through explicit user action

Once implemented, discovery review tooling should live in general project documentation, not only in roadmap notes.

## Constraints

- Keep the eligible universe explicit.
- Apply deterministic technical narrowing before expensive context work.
- Keep result counts capped.
- Keep scheduled discovery non-LLM.
- Keep discovery separate from execution.
- Preserve traceability from surfaced asset back to filter and ranking inputs.
- Keep token-consuming refinement user-initiated.
- Keep watch insertion explicit and user-visible.

## Non-Goals

- Auto-buy or auto-sell behavior
- Full-market mandatory AI scanning without pre-filtering
- Scheduled LLM refinement of discovery candidates
- Black-box learned ranking as the first implementation
- Strategy approval or rejection
- Hidden mutation of portfolio or watch state
- Unbounded historical storage of scan outputs

## Notes

This ADR should remain independently mergeable and user-releaseable when implemented.

Expected user-facing value:

- users receive a small ranked shortlist instead of scanning assets manually
- surfaced candidates include concise technical and context reasons
- promising names can move into watch monitoring without duplicate data entry
