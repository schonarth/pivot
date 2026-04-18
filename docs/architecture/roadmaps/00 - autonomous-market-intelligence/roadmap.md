---
name: Autonomous Market Intelligence Roadmap
description: Phased roadmap from asset-level news context to autonomous trading
type: reference
---

# Autonomous Market Intelligence Roadmap

Status: Approved

## Purpose

Define the end-state for Pivot's market intelligence system without forcing that full scope into a single ADR.

The target outcome is a paper-trading system that can:

1. Understand technical context for assets and portfolios
2. Understand evolving real-world news context beyond exact symbol mentions
3. Track narrative changes over time
4. Surface opportunities worth watching
5. Validate or reject trade ideas using technical + news context
6. Eventually execute autonomous paper trades under strict safety controls

This roadmap exists so each ADR can stay narrow while still pointing toward the same long-term vision.

## Vision

Pivot should eventually behave less like a static news summarizer and more like a disciplined market analyst:

- explain why an asset moved
- explain why the market ignored apparently relevant news
- keep track of multi-day narrative shifts
- monitor held assets and watched assets
- identify new assets worth monitoring
- transform context into bounded, auditable trading decisions

The near-term goal is not "full autonomy." The near-term goal is a sequence of small, testable capabilities that compound toward autonomy.

## Product Principles

- Keep context small and curated
- Prefer deterministic selection over broad retrieval
- Separate context building from reasoning from execution
- Preserve auditability at every step
- Expand scope from asset -> portfolio -> watchlist -> strategy
- Make safety controls stricter as automation increases
- Stay paper-trading only until autonomous behavior proves stable

## End-State Capabilities

The final system should support all of the following:

1. Asset intelligence
   - technical indicators
   - multi-layer news context
   - concise explanation of recent behavior

2. Portfolio intelligence
   - held-assets monitoring
   - portfolio-level macro exposure
   - prioritized events and risks

3. Watch intelligence
   - watched assets without open positions
   - news and technical monitoring
   - entry-readiness signals

4. Discovery intelligence
   - find new assets worth watching
   - rank opportunities by technical + sentiment + macro relevance

5. Strategy intelligence
   - convert context into trade validation
   - generate bounded scenarios and rationale
   - support backtests and paper-only dry runs

6. Autonomous trading
   - execute strategy-driven paper trades
   - enforce hard risk limits
   - maintain full execution history and rationale

## Milestone Structure

Each milestone below is S.M.A.R.T.:

- Specific: one narrow capability
- Measurable: explicit exit criteria
- Achievable: limited technical surface area
- Relevant: directly advances the end-state
- Time-bound: intended to fit inside a short implementation window

Suggested cadence:

- Small milestone: 1 ADR, 1 implementation cycle, 1-2 weeks
- Medium milestone: 1 ADR plus follow-up implementation hardening, 2-3 weeks

## Releaseability

Milestones should be independently mergeable to `main`, but not every milestone should be treated as an end-user release on its own.

This roadmap uses three releaseability labels:

- `User-releaseable`: delivers clear user-visible value and can ship as a standalone release
- `Mergeable foundation`: safe to merge to `main`, but mostly enables later milestones
- `Internal only`: should usually ship behind a flag or be bundled with a user-facing milestone

Rule:

- every milestone must be mergeable
- user-visible releases should happen whenever a milestone materially improves analysis, monitoring, or trading behavior
- foundational milestones should explicitly name the first user-facing milestone that depends on them

## Milestone 0: Baseline and Interfaces

Objective:
Create the system boundaries needed for later intelligence work without changing product behavior.

Scope:

- define context-builder responsibility
- define analysis input/output shape
- define storage boundaries for news, technical signals, and analysis artifacts
- identify current consumers: per-asset analysis
- reserve future consumers: portfolio, watchlist, strategy

Out of scope:

- new trading behavior
- new recommendation behavior
- autonomous decisions

Target window:
- 1 week

Releaseability:
- `Mergeable foundation`
- First user-facing dependent milestone: Milestone 1

Exit criteria:

- one ADR defines the boundary between context selection, reasoning, and execution
- one reference document defines shared vocabulary: asset scope, portfolio scope, watch scope, strategy scope
- current per-asset analysis still works with no behavior expansion

## Milestone 1: Asset Context Expansion

Objective:
Improve asset analysis by expanding beyond symbol-only news.

Primary ADR:
- ADR-001 Open News Context Expansion

Scope:

- symbol-level news
- company-name news
- sector news
- industry news
- market/macro news
- theme keywords
- deterministic deduplication and ranking
- tagged context provenance

Out of scope:

- multi-day narrative tracking
- recommendations
- scenario generation
- autonomous actions

Target window:
- 1-2 weeks

Releaseability:
- `User-releaseable`
- User value: better asset explanations when the driver is sector, macro, or theme news rather than symbol-only headlines

Exit criteria:

- each asset analysis request can supply a compact context pack with tagged items
- prompt size stays within a defined cap
- context quality improves for assets affected by sector or macro events with no symbol mention
- at least 3 representative assets from different markets validate the broader context behavior

## Milestone 2: Temporal Narrative Continuity

Objective:
Add short-memory narrative continuity so analysis can explain what changed, not just what exists.

Primary ADR:
- ADR-002 Narrative Continuity for Asset Context

Scope:

- timestamp all selected context items
- define short lookback window
- optionally capture basic headline sentiment at ingestion time if it does not complicate the milestone:
  - `positive`
  - `neutral`
  - `negative`
- if sentiment is captured at ingestion, allow batched classification for a set of headlines in one LLM call when that reduces token or latency cost
- label items as new, continuing, or shifted
- add a compact "story so far" section to analysis prompts

Out of scope:

- full fact versioning
- probability models
- autonomous strategy decisions

Target window:
- 1-2 weeks

Releaseability:
- `User-releaseable`
- User value: explanations can say what changed across recent days instead of describing each day in isolation

Exit criteria:

- analysis can explain at least one multi-day narrative shift for an asset
- prompt includes short continuity context without materially increasing noise
- prior-day context reuse is bounded by explicit retention rules
- lookback window is explicitly bounded to a short range such as 3-7 days, with older items excluded or strongly decayed
- if ingestion-time sentiment is included, stored sentiment is available for later trajectory computation without historical backfill

## Milestone 3: Portfolio and Watch Scope

Objective:
Generalize intelligence from a single asset to a user-defined monitored set.

Primary ADR:
- ADR-003 Context Scope Expansion: Asset, Portfolio, Watchlist

Scope:

- define watchlist or watched-assets concept
- support context building for:
  - one asset
  - held assets in a portfolio
  - watched assets without position
- portfolio-level event prioritization
- avoid duplicate stories across multiple assets
- cluster shared macro or sector events when they affect multiple assets in the same monitored set

Out of scope:

- discovery of new assets not already held or watched
- autonomous trading

Target window:
- 2 weeks

Releaseability:
- `User-releaseable`
- User value: portfolio and watched-assets monitoring become first-class instead of forcing users to inspect each asset individually

Exit criteria:

- system can generate one portfolio intelligence summary and one watch summary from the same underlying pipeline
- watched assets can exist without open positions
- duplicate macro stories are clustered instead of repeated asset-by-asset
- clustered events can show the affected assets once, for example a single oil-sector event affecting `PETR4`, `PETR3`, and `RRRP3`

## Milestone 4: Sentiment Trajectory

Objective:
Track how sentiment changes over time for important themes and assets.

Primary ADR:
- ADR-004 Sentiment Trajectory and Narrative State

Scope:

- sentiment state per selected context item
- aggregate sentiment by theme or asset
- detect improving, deteriorating, conflicting, and reversing sentiment
- expose trajectory as analysis input, not execution logic

Out of scope:

- direct trade execution from sentiment alone
- complex ML training loops

Target window:
- 2 weeks

Releaseability:
- `User-releaseable`
- User value: users can see whether the narrative is improving, deteriorating, conflicting, or reversing instead of seeing only static sentiment

Exit criteria:

- system can identify at least these states: improving, deteriorating, conflicting, reversal
- analysis output can explain sentiment shift when price action diverges from headline tone
- trajectory data retained for a defined short historical window

## Milestone 5: Counterfactual and Divergence Reasoning

Objective:
Explain expected vs actual market behavior in a disciplined way.

Primary ADR:
- ADR-005 Divergence Reasoning for Market Analysis

Scope:

- define expected direction from technical + context inputs
- compare to actual move
- classify common divergence patterns:
  - no material follow-through
  - competing macro priority
  - reversal
  - uncertainty/conflict
- render divergence assessment with a compact UI disclosure explaining that cross-asset reasoning only considers the current asset plus assets explicitly present in the relevant portfolio or watch scope

Out of scope:

- direct strategy execution
- long-term self-learning system

Target window:
- 2 weeks

Releaseability:
- `User-releaseable`
- User value: analysis can explain why price action contradicted the apparent news, such as oil falling after a blockade announcement because the market prioritized peace signals over present disruption

Exit criteria:

- analysis can produce a bounded divergence explanation for selected examples
- divergence labels are auditable from stored inputs
- UI disclosure is present where divergence analysis is shown so users understand that broader cross-asset reasoning only uses the current asset and explicitly monitored assets in the relevant portfolio or watch scope
- explanation quality is reviewed against a small hand-picked set of concrete divergence examples, such as:
  - oil prices falling after a blockade headline because de-escalation signals dominated
  - an asset failing to rise after positive company news because the expected reaction showed no material follow-through inside the bounded window
  - a market index rising despite geopolitical risk because investors focused on the more probable near-term outcome

## Milestone 6: Opportunity Discovery

Objective:
Find assets worth watching before they are held.

Primary ADR:
- ADR-006 Opportunity Discovery Pipeline

Scope:

- technical pre-filter across larger universe
- context-aware ranking of shortlisted assets
- daily or scheduled "assets to watch" output
- explain why each asset surfaced

Out of scope:

- auto-buy behavior
- mandatory AI scan of entire market without prefiltering

Target window:
- 2-3 weeks

Releaseability:
- `User-releaseable`
- User value: users receive a ranked shortlist of assets worth watching instead of only monitoring existing holdings

Exit criteria:

- system can scan a defined asset universe and return a capped shortlist
- each surfaced asset includes concise technical + context rationale
- watchlist can be populated from discovery output without manual duplication

## Milestone 7: Strategy Validation Layer

Objective:
Turn intelligence into bounded trade validation before any autonomous execution.

Primary ADR:
- ADR-007 Strategy Validation with Technical and Context Inputs

Scope:

- strategy inputs: technical conditions, news context, sentiment trajectory
- verdict types: approve, reject, defer
- rationale generation
- paper-only recommendation logging

Out of scope:

- live autonomous trade execution
- user-invisible black-box approvals

Target window:
- 2-3 weeks

Releaseability:
- `User-releaseable`
- User value: users can test trade ideas against technical and context rules before any autonomous execution is allowed

Exit criteria:

- system can evaluate strategy candidates in paper mode with an auditable verdict
- every verdict stores the exact technical and context inputs used
- rejected and deferred cases are first-class outcomes, not failures

## Milestone 8: Scenario and Risk Framing

Objective:
Add bounded forward-looking reasoning without yet granting trade autonomy.

Primary ADR:
- ADR-008 Scenario Framing for Strategy Decisions

Scope:

- near-term catalysts
- limited scenario generation
- bounded probability bands or confidence bands
- risk framing tied to position sizing constraints

Out of scope:

- unconstrained prediction engine
- free-form portfolio management by AI

Target window:
- 2 weeks

Releaseability:
- `User-releaseable`
- User value: recommendations become more actionable and transparent because they are tied to explicit catalysts, scenarios, and uncertainty

Exit criteria:

- strategy validation can attach scenarios to a recommendation
- each scenario references concrete catalysts or conditions
- uncertainty is explicit when context is conflicting or incomplete

## Milestone 9: Fact Corrections and Conflict Detection

Objective:
Add correction safety before granting autonomous execution.

Primary ADR:
- ADR-009 Fact Corrections and Conflict Detection

Scope:

- conflict detection for important facts
- manual correction workflow for outdated or contradicted context
- structured visibility into uncertain facts before strategy execution
- operator-visible failure modes for unstable analysis inputs

Out of scope:

- self-improving strategy behavior
- full autonomous trading execution

Target window:
- 2 weeks

Releaseability:
- `Mergeable foundation`
- First user-facing dependent milestone: Milestone 10

Exit criteria:

- conflicting facts can be marked and corrected without erasing history
- analysis and strategy layers can surface uncertainty instead of asserting unstable facts
- correction state is visible to operators before autonomous execution is enabled

## Milestone 10: Autonomous Paper Trading

Objective:
Enable fully automated paper trades driven by strategy + intelligence, under hard limits.

Primary ADR:
- ADR-010 Autonomous Paper Trading Controls

Scope:

- enable/disable autonomous mode per strategy
- scheduled evaluation
- trade execution in paper portfolio only
- safety rails:
  - daily loss limit
  - max position size
  - market-hours controls
  - cooldowns
  - kill switch
- full rationale and audit trail for every autonomous trade

Out of scope:

- real-money trading
- hidden or non-auditable execution

Target window:
- 2-3 weeks

Releaseability:
- `User-releaseable`
- User value: users can enable bounded autonomous paper trading with full auditability and hard safety limits

Exit criteria:

- autonomous strategies can execute paper trades under configured limits
- every trade records the triggering context, validation verdict, correction state, and safety checks
- kill switch and hard-stop conditions are tested
- weekly autonomous summary available for review

## Milestone 11: Learning, Review, and Operational Trust

Objective:
Make the system reliable enough to monitor and improve without losing transparency.

Primary ADR:
- ADR-011 Analysis Review and Operational Learning

Scope:

- structured review of analysis quality
- traceable review of incorrect or weak recommendations
- operator-visible failure modes and recurring patterns
- learning workflows that improve prompts, thresholds, or rules without hidden self-modification

Out of scope:

- self-modifying strategy behavior without review

Target window:
- 2 weeks

Releaseability:
- `Internal only`
- Usually bundled with Milestone 10 or a later user-facing reliability release

Exit criteria:

- analysis errors can be reviewed with traceable inputs
- recurring failure patterns can be categorized and prioritized
- system improvements remain reviewable and operator-controlled

## Dependency Order

Recommended order:

1. Milestone 0
2. Milestone 1
3. Milestone 2
4. Milestone 3
5. Milestone 4
6. Milestone 5
7. Milestone 6
8. Milestone 7
9. Milestone 8
10. Milestone 9
11. Milestone 10
12. Milestone 11

Allowed overlaps:

- Milestone 3 can begin once Milestone 1 is stable
- Milestone 4 can begin once Milestone 2 is stable
- Milestone 6 can begin once Milestone 3 and Milestone 4 are stable
- Milestone 10 requires Milestone 9 safety work to be stable first

## ADR Mapping

This roadmap should not replace ADRs. It should constrain them.

Rules for future ADRs:

1. Each ADR should map to exactly one milestone
2. Each ADR should state what it explicitly does not solve yet
3. Each ADR should describe the next consumer of the capability
4. Each ADR should keep storage, reasoning, and execution concerns separate

## Execution

Milestone execution should follow the reusable process defined in:

- [Milestone Delivery Execution Model](../../execution/milestone-delivery-execution-model.md)

That document defines:

- milestone folder structure
- spec file template
- status model and ownership
- testing policy
- blocker and escalation rules
- branching and UAT readiness

## Success Metrics by Stage

Early-stage metrics:

- asset analyses reference broader context without prompt bloat
- repeated daily analyses preserve narrative continuity
- portfolio and watch summaries avoid duplicate noise

Mid-stage metrics:

- sentiment reversals and conflicting signals are visible
- counterfactual explanations improve analyst trust
- opportunity shortlist quality is good enough to review daily

Late-stage metrics:

- strategy validation rejects bad trades reliably
- autonomous paper trading stays inside configured limits
- users can review exactly why autonomous trades happened

## Current Recommendation

Immediate next step:

- keep ADR-001 focused on Milestone 1
- optionally pull a minimal timestamped continuity hook from Milestone 2 if it does not complicate the ADR

Do not pull these into ADR-001:

- opportunity discovery
- scenario generation
- strategy execution
- autonomous trading controls
- full correction and learning system

## Related Documents

- [ADR-001 Open News Context Expansion](../../adrs/ADR-001-open-news-context-expansion.md)
- [Milestone Delivery Execution Model](../../execution/milestone-delivery-execution-model.md)
- [Deferred Improvements](deferred-improvements.md)
- [PRD — Paper Trader](../../../reference/prd-paper-trader.md)
- [PRD — MLP Phase](../../../reference/prd-mlp.md)
- [Specification](../../../reference/specification.md)

## ADR Readiness Checklist

Draft a milestone ADR only when most of the following are true:

- the milestone has a clear user or system outcome
- the milestone boundary is small enough to discuss without relying on later milestones
- the main consumer of the capability is known
- the likely storage, reasoning, and execution boundaries are understood
- non-goals can be stated clearly
- the main alternatives or tradeoffs are visible
- open questions are specific enough to resolve in one ADR
- success or exit criteria can be stated concretely
- the team is likely to work on the milestone soon

Prefer not to draft the ADR yet when any of these are true:

- the milestone depends heavily on learning from an earlier milestone
- the likely shape is still speculative
- the document would mostly repeat the roadmap
- the milestone has no clear consumer yet
