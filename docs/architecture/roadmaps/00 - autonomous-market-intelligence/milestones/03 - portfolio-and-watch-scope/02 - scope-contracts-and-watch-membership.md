# 02 - Scope Contracts and Watch Membership

## Purpose

Define the minimum scope contract and explicit watch membership model needed to support `asset`, `portfolio`, and `watch` without expanding into discovery work.

## Roadmap Milestone

Milestone 03 - Portfolio and Watch Scope

## Governing ADR

ADR-003 Context Scope Expansion: Asset, Portfolio, Watchlist

## Status

planned

## Owner

unassigned

## Branch

feat/autonomous/03-scope-expansion

## Dependencies

- 00 - milestone coordination.md
- 01 - monitored-set-consumers-and-insertion-points.md

## Required Prior References

- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces/02 - shared-vocabulary-and-interface-contracts.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces/03 - current-consumers-and-storage-touchpoints.md`
- `docs/architecture/adrs/ADR-003-context-scope-expansion-asset-portfolio-watchlist.md`

## Likely Files Touched

- backend/ai/*
- backend/portfolios/*
- backend/markets/*
- backend/mcp/*
- frontend/src/*
- docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/03 - portfolio-and-watch-scope/02 - scope-contracts-and-watch-membership.md

## Entry Conditions

- insertion point documented
- milestone coordination reviewed
- required prior references reviewed

## Background

ADR-003 approves explicit monitored-set membership and a shared scope contract, but the implementation still needs one concrete contract for input shape, watch membership, and minimal persistence.

## Detailed Requirements

- define the minimum scope contract for context building:
  - `scope_type`
  - `scope_id`
  - `as_of`
- define deterministic membership rules for:
  - `asset`
  - `portfolio`
  - `watch`
- specify the minimum watch-scope representation required for this milestone
- keep watch scope distinct from portfolio holdings
- avoid introducing discovery or inferred membership behavior
- define any minimal API, serializer, model, or UI contract changes needed for explicit watch membership
- use a dedicated watch persistence model for this milestone:
  - one user-owned `WatchScope`
  - one join model such as `WatchMembership`
- keep persistent storage narrow and justified

## Proposed Approach

- reuse existing scope vocabulary from Milestone 00
- define watch scope as an explicit user-owned monitored asset set with minimal metadata
- persist watch scope with dedicated tables rather than overloading `Portfolio` or storing raw asset ID lists in user settings
- prefer the smallest persistence change that makes watch membership durable and auditable
- if multiple persistence options exist, choose the one that least disturbs current portfolio and asset flows
- document the contract in a way later milestones can reuse without renaming fields

## Validation Scenarios

- a portfolio scope deterministically resolves to currently held assets
- a watch scope deterministically resolves to explicitly attached assets without open positions
- the same asset can appear in both a portfolio and a watch scope
- no part of the contract implies inferred discovery behavior
- watch membership remains durable, auditable, and independent of portfolio lifecycle
- downstream tasks can compose monitored-set context from this contract without revisiting membership semantics

## Task Steps

1. Confirm the minimal scope contract shape and where it enters the producer path.
2. Define deterministic membership rules for each scope type.
3. Define the minimum watch-scope persistence and API surface required for this milestone.
4. Identify likely backend and frontend contract changes while keeping them as small as possible.
5. Call out rejected options that would introduce inferred discovery or oversized persistence.

## Tests to Add or Update

- contract tests for scope resolution
- membership tests for portfolio-held and watch-attached assets
- serializer or API tests for explicit watch membership surfaces

## Commands to Run

- `cd backend && ruff check .`
- run affected backend tests around portfolios, assets, and any watch membership models or APIs
- `cd frontend && npm run typecheck` if frontend files are touched

## Exit Conditions

- scope contract is explicit and reusable
- watch membership model is explicit and deterministic
- minimal persistence boundary is documented
- later clustering and implementation tasks can rely on stable scope semantics

## Implementation Notes / What Was Done

Not started.

## Open Follow-Ups

- default to one named default watch scope for the first release unless the code scan shows multiple named sets are almost free
