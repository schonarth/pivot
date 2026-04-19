---
name: Deferred Improvements
description: Deferred implementation and operational improvements for the autonomous market intelligence roadmap
type: reference
---

# Deferred Improvements

Status: Active

## Purpose

Track intentionally deferred improvements discovered while planning or executing this roadmap.

Use this document for:

- future operational improvements
- intentionally postponed design refinements
- automation ideas that are directionally useful but not yet planned
- known quality improvements whose safest current answer is "defer"

Do not use this document for:

- accepted ADR decisions
- milestone task execution notes
- bugs that should be fixed immediately

## How To Use This Document

Each entry should include:

- a short title
- the roadmap context
- the current safe policy
- why the work is deferred
- the earliest milestone where it may be revisited
- the likely future direction
- the risk if it remains deferred too long

Entries here are not approved work by default. They are structured reminders of deliberate non-decisions.

---

## 001 - Asset Metadata Enrichment and Override Maintenance

### Context

Milestone 01 needs reliable sector and industry context to expand beyond symbol-only news. A strict deterministic approach is preferred, but manually maintaining rich metadata for every asset is out of scope.

### Current Safe Policy

- use stored asset metadata first
- use small explicit overrides for known gaps or mistakes
- if metadata is still insufficient, skip sector or industry expansion rather than infer loosely

### Why Deferred

- maintaining comprehensive asset classifications by hand creates operational burden
- automatic inference too early would weaken determinism and make analysis behavior harder to audit
- Milestone 01 should optimize for correctness over maximum coverage

### Earliest Revisit

- Milestone 01 implementation review
- more likely Milestone 03 or later, once broader monitored-asset scope increases pressure for better metadata coverage

### Future Direction

- ingestion-time metadata enrichment from upstream sources
- reporting for missing or low-quality metadata
- human-approved suggested overrides
- optional offline enrichment workflows with explicit review

### Risk If Deferred Too Long

- some assets will receive weaker context quality than others
- context quality may depend too heavily on whatever metadata happens to be present
- important assets with missing classification may underperform until explicitly patched

---

## 002 - Persisted News Artifacts Beyond Prompt-Time Assembly

### Context

Milestone 00 identifies likely storage touchpoints for news metadata, context artifacts, technical signals, and analysis outputs. For early milestones, prompt-time assembly is expected to remain the safe default, but later milestones may benefit from storing richer news artifacts.

### Current Safe Policy

- keep Milestone 00 and Milestone 01 focused on prompt-time context assembly where possible
- do not introduce persistent news-artifact storage unless a later milestone proves it is necessary

### Why Deferred

- persistent storage introduces schema, lifecycle, and consistency questions too early
- early milestones should first prove the value of context selection before broadening storage responsibilities
- premature persistence risks creating duplicate storage paths or overcommitting to the wrong abstraction

### Earliest Revisit

- Milestone 03 or later
- sooner only if Milestone 01 or 02 implementation shows prompt-time assembly is no longer sufficient

### Future Direction

- persist curated news artifacts only when a later milestone needs durable reuse
- distinguish raw fetched data from curated context items
- define retention, freshness, and invalidation rules before introducing persistence

### Risk If Deferred Too Long

- later milestones may lack reusable historical context if prompt-time assembly proves too thin
- teams may create ad hoc persistence in multiple places if the need becomes urgent without a shared decision

---

## 003 - Typed Context Pack Contract

### Context

Milestone 00 establishes shared vocabulary and minimum interface contracts, but stops short of requiring a fully typed backend contract for the context pack.

### Current Safe Policy

- keep the context pack minimally specified and stable enough for Milestone 01
- avoid introducing a premature typed contract unless the implementation clearly benefits from it

### Why Deferred

- a typed contract is useful only once the shape has proven stable enough
- early milestones may still refine field names, optional metadata, and consumer needs
- locking in a contract too soon may increase churn instead of reducing it

### Earliest Revisit

- Milestone 01 implementation review
- more likely Milestone 02 or 03, once multiple consumers need the same shape

### Future Direction

- promote the context pack into a typed backend contract when multiple layers depend on it
- validate the contract against more than one consumer before hardening it
- keep storage, reasoning, and execution boundaries intact when formalizing the type

### Risk If Deferred Too Long

- multiple consumers may drift into slightly different context-pack assumptions
- later refactors may become harder if the shape is used widely without an explicit contract

---

## 004 - RSS Source Management and Feed Operations

### Context

News collection currently needs a pragmatic, low-friction path that yields enough headlines for asset analysis. Query-based RSS is a good short-term fit, but source quality, duplication, locale coverage, and provider drift will need operational management over time.

### Current Safe Policy

- allow simple code-level RSS source configuration that restores headline flow
- prefer accessible feeds over brittle HTML scraping in the critical ingestion path
- keep source selection deterministic and lightweight for now

### Why Deferred

- proper source management introduces operational concerns beyond the immediate fix:
  - source onboarding and retirement
  - per-market locale tuning
  - feed health monitoring
  - duplicate-source suppression
  - source quality scoring
- this work is useful, but not required to prove that headline ingestion is functioning again
- the immediate priority is restoring non-zero headline volume without creating a new management surface prematurely

### Earliest Revisit

- Milestone 01 or 02 implementation hardening
- more likely before broader portfolio and watch-scope rollout in Milestone 03, when source volume and duplication pressure increase

### Future Direction

- define explicit RSS source registries by market, locale, and query purpose
- support source priorities, caps, and failover rules
- track feed health and last successful ingest
- expose operator-visible controls for enabling, disabling, or tuning sources without code edits
- distinguish asset-specific, sector, macro, and theme-oriented feed inputs

### Risk If Deferred Too Long

- source drift may silently reduce headline quality or coverage
- duplicate or low-signal feeds may inflate prompt noise
- adding new markets or monitored scopes may become operationally clumsy without a clearer source-management model

---

## 005 - OHLCV Backfill Settings Card Refinements

### Context

Milestone 02 now exposes OHLCV backfill status in Settings so operators can start and observe history catch-up. The current card is intentionally functional first, but it can become quieter and more informative once the backfill path proves stable.

### Current Safe Policy

- keep the existing Settings card simple and readable
- show live progress while backfill is actively running
- avoid adding extra UI states unless they help with operator clarity

### Why Deferred

- the current live log is useful during catch-up but noisy once backfill finishes
- filtering down to failed entries or summarizing completion would require extra display rules
- subtle presentation changes are valuable, but not on the critical path for proving the backfill itself

### Earliest Revisit

- after backfill behavior has settled in normal use
- ideally alongside a broader Settings polish pass

### Future Direction

- hide the processed-entry log once backfill completes
- show only failed entries after completion
- replace repeated log rows with a compact summary when the queue is idle
- surface a small last-run summary instead of the full historical log

### Risk If Deferred Too Long

- the card may stay noisier than necessary for operators
- the Settings page could feel heavier than the underlying feature warrants
- repeated full logs may distract from higher-value configuration controls

## 006 - Portfolio and Watch UI Polish

### Context

Milestone 03 now has a true portfolio-level and watch-level AI summary UI, but the first pass favors capability over finish. The current shape is functional, yet it still needs refinement in layout hierarchy, tab navigation clarity, and overall visual cleanliness.

### Current Safe Policy

- keep the current monitored-set intelligence behavior intact
- preserve portfolio summary, watch summary, and asset drill-down
- defer visual polish until after the milestone is accepted and the user flow is stable

### Why Deferred

- the first pass needed to prove the monitored-set AI summaries and watch binding
- layout and navigation refinements are valuable, but they are not blockers for the core milestone outcome
- the current implementation is good enough to use, so the safest next step is a focused UX pass rather than more structural change

### Earliest Revisit

- immediately after Milestone 03 acceptance
- before starting Milestone 04 work

### Future Direction

- simplify the portfolio page hierarchy so the AI summary reads as the primary scope result
- tighten tab navigation and tab labels so positions, watches, and drill-down feel obvious
- reduce visual clutter in the portfolio detail page and asset detail controls
- align spacing, card density, and button placement for a cleaner browsing flow

### Risk If Deferred Too Long

- the current UI may feel busy or confusing even though the underlying capability is correct
- users may miss the scope-level summary because the drill-down remains prominent
- the new monitored-set experience may feel more like a convenience feature than the primary portfolio/watch analysis surface

---

## 007 - Specialized Watch Lists for Close Tracking vs Breadth

### Context

Milestone 03 chose the smallest safe watch-scope shape: one named default watch scope per user unless multiple named sets were nearly free. That was appropriate when watch scope mainly needed to support one monitored-set summary. Milestone 05 raises a new pressure: divergence assessment becomes stronger when users monitor a broader peer set, but many users will still want a much smaller set of assets they follow closely day to day.

### Current Safe Policy

- keep the current single watch-scope behavior intact
- continue treating watch membership as explicit and user-controlled
- use UI disclosure to explain that divergence reasoning only considers the current asset plus explicitly monitored assets in the relevant portfolio or watch scope

### Why Deferred

- the current single-list model is still sufficient to keep Milestone 03 and Milestone 05 honest
- adding multiple watch lists introduces naming, navigation, empty-state, and migration questions that are not required to prove divergence reasoning itself
- broadening watch management too early risks turning a focused analysis milestone into a larger product-surface change

### Earliest Revisit

- after Milestone 05 acceptance
- before or alongside any later work that depends more heavily on cross-asset monitored breadth

### Future Direction

- allow at least two user-managed watch lists or equivalent watch modes
- support one narrow list for close tracking and one broader list for context enrichment
- keep membership explicit rather than inferred
- preserve a simple default setup for users who do not want to manage multiple lists
- consider fully user-managed named watch lists, since users may cluster assets more cleanly by theme, such as energy, tech, media, or other cohorts
- that shape can produce cleaner analyses than forcing everything into a single bucket, even if we offer two buckets
- possible product framing:
  - close watch vs context watch
  - primary watch vs broader watch
  - fully user-managed named watch lists if that proves cleaner than fixed two-list semantics

### Risk If Deferred Too Long

- users may hesitate to add helpful peer assets because doing so pollutes the one list they actually use for close monitoring
- Milestone 05 divergence explanations may stay thinner than they need to be because users keep their watch scope artificially small
- the product may push users toward a behavior that improves analysis quality while making their everyday watch workflow worse

---

## 008 - Distinguish No Expectation From Flat Expectation

### Context

The current divergence model uses `expected_direction = none` when it could not form a directional expectation. That works for "no signal" cases, but it becomes ambiguous when the actual move is flat, because `none + flat` can look like an implied match even though no flat expectation was ever made.

### Current Safe Policy

- keep `expected_direction` as the only expectation field for now
- treat `none` as "no directional expectation formed"
- keep `flat` as an actual outcome only, not a modeled expectation state

### Why Deferred

- the current model is simple and sufficient for Milestone 05 behavior
- adding a separate expectation state changes the data model, the analysis logic, and the UI copy
- the distinction is useful, but not required to prove divergence reasoning itself

### Earliest Revisit

- when we want to make flat outcomes easier to interpret in the UI
- before adding any richer divergence badges or expectation-state analytics

### Future Direction

- introduce a separate expectation state such as `no_signal`, `flat`, `up`, `down`
- or add a boolean like `has_directional_expectation`
- preserve the ability to say "we had no expectation" versus "we expected flat"

### Risk If Deferred Too Long

- users may misread `none + flat` as a positive match instead of a lack of signal
- the divergence card may stay slightly ambiguous in low-signal cases
- future copy may need to keep explaining a distinction the model does not encode directly
