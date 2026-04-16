# 02 - Shared Vocabulary and Interface Contracts

## Purpose

Define shared terms and minimum interface contracts so later roadmap milestones use the same language and integration points.

## Roadmap Milestone

Milestone 00 - Baseline and Interfaces

## Governing ADR

Roadmap-only planning task for Milestone 00 baseline work.

## Status

planned

## Owner

unassigned

## Branch

feat/autonomous/00-baseline

## Date Started

not started

## Date Completed

not started

## Dependencies

- 00 - milestone coordination.md
- 01 - boundary-decision-and-current-state-scan.md

## Likely Files Touched

- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces/02 - shared-vocabulary-and-interface-contracts.md
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/roadmap.md
- docs/architecture/adrs/ADR-001-open-news-context-expansion.md

## Entry Conditions

- baseline boundary scan complete
- current consumers identified

## Background

The roadmap now spans asset analysis, portfolio monitoring, watch functionality, strategy validation, and autonomous execution. Those later milestones will become harder to coordinate if they use overlapping words with different meanings. This task creates a small shared language and minimum interface assumptions so later ADRs and implementation specs stop arguing about basic terms.

## Detailed Requirements

- define a compact vocabulary for the scopes already named by the roadmap:
  - asset scope
  - portfolio scope
  - watch scope
  - strategy scope
- define core objects used across milestones:
  - context item
  - context pack
  - analysis input
  - analysis output
- define minimal contracts for:
  - what the context builder receives
  - what it returns
  - what the reasoning layer consumes
  - what execution layers must not infer implicitly
- keep these contracts narrow enough that Milestone 01 is not overdesigned
- avoid locking in database schemas or API payloads prematurely unless the codebase already forces them

## Proposed Approach

- reuse the boundary language established in the previous task
- align terms with the roadmap and ADR-001 instead of creating a second vocabulary
- prefer short definitions and field lists over long prose
- call out optional versus required fields where uncertainty remains
- document explicit non-assumptions if later milestones are expected to refine a contract

## Validation Scenarios

- a Milestone 01 task should be able to say “context pack” and have one agreed meaning
- a future portfolio milestone should be able to reuse “context item” without redefining it
- an execution-layer task should be able to identify which outputs are analysis artifacts versus actionable decisions
- the vocabulary should be small enough that an agent can hold it in working memory without carrying the whole roadmap

## Task Steps

1. Define a compact vocabulary for:
   - asset scope
   - portfolio scope
   - watch scope
   - strategy scope
   - context item
   - context pack
   - analysis output
2. Define minimum contracts for later milestones:
   - what a context builder receives
   - what a context builder returns
   - what an analysis layer consumes
   - what execution layers must not assume
3. Keep contracts technology-agnostic where possible.
4. Avoid overdesigning fields that later milestones have not validated yet.
5. Cross-check the vocabulary against ADR-001 and roadmap language.

## Tests to Add or Update

- docs-only baseline task
- no direct unit tests expected unless code is touched to formalize interfaces

## Commands to Run

- if code is touched: run relevant lint, typecheck, and affected tests

## Exit Conditions

- shared vocabulary is unambiguous
- later milestones can reference one common set of terms
- minimum contracts exist for context input and output without locking in premature implementation detail

## Implementation Notes / What Was Done

Not started.

## Open Follow-Ups

- see Deferred Improvements `003 - Typed Context Pack Contract`
