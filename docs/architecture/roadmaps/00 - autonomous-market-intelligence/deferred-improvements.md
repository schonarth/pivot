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
