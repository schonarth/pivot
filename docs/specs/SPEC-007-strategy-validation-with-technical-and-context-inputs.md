---
name: Strategy Validation with Technical and Context Inputs
description: Spec for bounded paper-only trade validation using technical conditions, context, and sentiment trajectory
type: reference
---

# SPEC

## SPEC-007 Strategy Validation with Technical and Context Inputs

Status: Approved
Governing ADR: [ADR-007-bounded-strategy-validation](../adrs/ADR-007-bounded-strategy-validation.md)

## Roadmap Position

This SPEC corresponds to Milestone 7 of the Autonomous Market Intelligence roadmap:

- [Autonomous Market Intelligence Roadmap](../roadmaps/00%20-%20autonomous-market-intelligence/roadmap.md)

Its role is narrow: validate a proposed trade idea against bounded technical and context evidence before any autonomous execution is allowed.

It is not intended to execute trades, replace the earlier analysis pipeline, or create a black-box approval system.

## Context

SPEC-001 broadens context selection. SPEC-002 adds bounded continuity. SPEC-003 expands monitored-set scope. SPEC-004 adds sentiment trajectory. SPEC-005 adds divergence reasoning. SPEC-006 adds opportunity discovery.

That still leaves a gap: the system can now explain assets, monitored sets, divergences, and discovery candidates, but it cannot yet validate a proposed trade idea in a disciplined way before autonomous execution or recommendation logging.

Users eventually need answers such as:

- should this paper-trade idea be approved now
- does the current technical setup support the proposed direction
- does the current context strengthen or weaken the idea
- is there enough evidence to defer rather than force a yes or no

Without a bounded validation layer, the system can analyze markets, but it cannot turn that analysis into an auditable paper-only decision workflow.

## Decision

Milestone 7 should add a deterministic strategy-validation layer on top of the existing intelligence inputs.

That layer should:

1. accept a bounded strategy candidate with explicit trade intent
2. evaluate the candidate against technical conditions, news context, and sentiment trajectory
3. classify the result into one of three verdicts:
   - `approve`
   - `reject`
   - `defer`
4. store the exact input snapshot and verdict for paper-only review
5. expose rationale as analysis output, not as execution authority

The validation layer should stay small, auditable, and paper-only. It should not become an autonomous order router or a hidden approval engine.

The first consumer should be:

1. paper-strategy review and recommendation logging

Future milestones may reuse the same validation contract later for:

1. scenario framing
2. autonomous execution gating

## Intended Shape

The future implementation should treat strategy validation as a bounded decision layer that sits after the analysis pipeline and before any future autonomous execution layer.

Expected flow:

1. build the current analysis inputs
2. receive an explicit strategy candidate
3. evaluate technical conditions against the candidate
4. evaluate current context and sentiment trajectory against the candidate
5. emit a compact verdict with rationale
6. persist the exact inputs used for that verdict in paper-only logs

The strategy-validation output should remain compact and reviewable. It should not require storing a free-form reasoning transcript as the system of record.

### Manual Trade UI Must Stay Opt-In

If strategy validation is surfaced in the manual trade flow, it should appear as an explicit opt-in action near the existing `BUY` or `SELL` execute controls.

Recommended shape:

- a conspicuous `Should I?` button near the trade execution action
- no automatic validation call on trade-form load or field change
- no hidden validation request as part of manual trade execution

Meaning:

- validation consumes extra processing time and tokens, so the user should decide when to request it
- manual trade authority remains with the user
- a returned `approve`, `reject`, or `defer` verdict is advisory only in the manual trade flow
- the user must still be able to execute the trade regardless of the validation verdict

## Resolved Decisions

### Strategy Validation Must Consume Explicit Candidates

Milestone 7 should validate a candidate that already exists. It should not invent the trade idea from the analysis output.

Meaning:

- the candidate must describe the proposed action explicitly
- the candidate must be bounded enough for deterministic evaluation
- the validation layer should not infer hidden intent from prose

This keeps the system from quietly turning analysis into execution logic.

### Verdicts Must Stay Small and Auditable

Milestone 7 should use only these verdicts:

- `approve`
- `reject`
- `defer`

Meaning:

- `approve`: the candidate satisfies the required technical and context conditions
- `reject`: the candidate violates one or more hard requirements
- `defer`: the candidate is not clearly wrong, but the evidence is insufficient or too conflicted for an immediate recommendation

This milestone should prefer a small verdict vocabulary over a broader scoring taxonomy.

### Paper-Only Recommendation Logging Is Required

Milestone 7 should persist every verdict as a paper-only recommendation record.

The record should capture at minimum:

- the candidate identity
- the strategy inputs used
- the technical inputs used
- the context inputs used
- the sentiment trajectory inputs used
- the final verdict
- a compact rationale

Reason:

- users need an audit trail for why a candidate was approved, rejected, or deferred
- the later autonomous layer should be able to reuse the same evidence boundary
- paper-only logging keeps strategy validation visible without authorizing execution

### Existing Analysis Inputs Should Be Reused

Milestone 7 should build on the earlier analysis pipeline rather than recomputing a separate market understanding stack.

Meaning:

- technical conditions come from the existing technical analysis surface
- news context comes from the existing context-building surface
- sentiment trajectory comes from the existing short-window trajectory surface
- strategy validation should not introduce a parallel context store

The validation layer should reuse stored analysis artifacts whenever possible and only add the minimum candidate-specific structure needed for a decision.

### Deferred and Rejected Are First-Class Outcomes

Milestone 7 should treat `defer` as a real verdict, not as a failure mode.

Meaning:

- unclear evidence should not be forced into a false `approve` or `reject`
- a deferred candidate may be revisited later when context changes
- a rejected candidate should remain auditable rather than disappearing from the workflow

This keeps the system honest when the evidence is incomplete or conflicting.

### Validation Output Must Be Structured First

Milestone 7 should emit structured validation records first, with optional small display text layered on top.

Recommended minimum fields:

- `candidate_id`
- `asset_id`
- `verdict`
- `technical_inputs`
- `context_inputs`
- `sentiment_trajectory_inputs`
- `rationale`
- `recorded_at`

Meaning:

- `technical_inputs`: the compact structured technical evidence used in validation
- `context_inputs`: the bounded context summary used in validation
- `sentiment_trajectory_inputs`: the bounded trajectory summary used in validation
- `rationale`: concise display-oriented explanation of the verdict

User-facing prose may summarize the result, but prose should not become the canonical strategy record.

### Execution Boundary Must Stay Closed

Milestone 7 should not place any order or alter any position.

Not approved in this milestone:

- live trade execution
- autonomous order placement
- blocking manual trade execution based on validation output
- user-invisible approval flows
- hidden strategy scoring that cannot be inspected later

The output is a recommendation record, not an execution side effect.

### Validation and Review

Milestone 7 should be validated with deterministic fixtures and a simple paper-review workflow.

Fixture guidance:

- unit tests should use frozen curated fixtures as the regression source of truth
- each fixture should include the candidate inputs and the expected verdict
- fixtures should cover at least one clear approve case, one clear reject case, and one defer case

Review guidance:

- the paper-review surface should show the exact inputs and the stored verdict together
- the rationale should be short enough to inspect without opening a separate reasoning log
- the review surface should make it easy to confirm that the verdict matches the stored evidence

## Constraints

- Keep strategy validation bounded to the existing analysis inputs.
- Keep verdicts small and auditable.
- Keep paper-only logging canonical.
- Reuse technical, context, and trajectory artifacts where possible.
- Keep validation separate from execution.
- Keep any manual-trade integration opt-in and non-blocking.

## Non-Goals

- Live autonomous trade execution
- Hidden or non-auditable approvals
- Long-horizon portfolio management by AI
- Unbounded strategy generation
- Free-form prediction engines

## Notes

This SPEC should remain independently mergeable and user-releaseable when implemented.

Expected user-facing value:

- users can test trade ideas against technical and context rules before any autonomous execution is allowed
- users can optionally request `Should I?` guidance near manual trade execution without surrendering final trade authority
