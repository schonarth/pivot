# 02 - Scope Contracts and Watch Membership

## Purpose

Define the minimum scope contract and explicit watch membership model needed to support `asset`, `portfolio`, and `watch` without expanding into discovery work.

## Roadmap Milestone

Milestone 03 - Portfolio and Watch Scope

## Governing SPEC

SPEC-003 Context Scope Expansion: Asset, Portfolio, Watchlist

## Status

done

## Owner

GPT-5 / docs

## Branch

feat/autonomous/03-scope-expansion

## Date Started

2026-04-16

## Date Completed

2026-04-16

## Dependencies

- 00 - milestone coordination.md
- 01 - monitored-set-consumers-and-insertion-points.md

## Required Prior References

- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces/02 - shared-vocabulary-and-interface-contracts.md`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces/03 - current-consumers-and-storage-touchpoints.md`
- `docs/specs/SPEC-003-context-scope-expansion-asset-portfolio-watchlist.md`

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

SPEC-003 approves explicit monitored-set membership and a shared scope contract, but the implementation still needs one concrete contract for input shape, watch membership, and minimal persistence.

## Detailed Requirements

- define the minimum scope contract for context building:
  - `scope_type`
  - `scope_id`
  - `as_of`
- make the scope contract deterministic and closed:
  - `scope_type` must be one of `asset`, `portfolio`, `watch`
  - `scope_id` must resolve to the canonical identifier for the selected scope type
  - `as_of` must be the evaluation boundary used for membership resolution
- define deterministic membership rules for:
  - `asset`
  - `portfolio`
  - `watch`
- keep watch scope distinct from portfolio holdings
- avoid introducing discovery or inferred membership behavior
- specify the smallest explicit watch persistence boundary needed for this milestone
- keep persistent storage narrow and auditable

## Proposed Approach

- reuse existing scope vocabulary from Milestone 00
- define `asset` scope as a single-asset singleton, `portfolio` scope as positions at `as_of`, and `watch` scope as an explicit user-owned monitored asset set
- persist watch scope with one user-owned `WatchScope` row and one join model such as `WatchMembership`
- prefer the smallest persistence change that makes watch membership durable, explicit, and auditable
- reject raw asset-id lists in user settings and any portfolio-based watch reuse
- document the contract in a way later milestones can reuse without renaming fields

## Validation Scenarios

- an asset scope resolves to exactly one asset
- a portfolio scope deterministically resolves to currently held assets at `as_of`
- a watch scope deterministically resolves to explicitly attached assets without open positions
- the same asset can appear in both a portfolio and a watch scope
- no part of the contract implies inferred discovery behavior
- watch membership remains durable, auditable, and independent of portfolio lifecycle
- downstream tasks can compose monitored-set context from this contract without revisiting membership semantics

## Task Steps

1. Confirm the minimal scope contract shape and where it enters the producer path.
2. Define deterministic membership rules for `asset`, `portfolio`, and `watch`.
3. Define the smallest explicit watch persistence boundary needed for durable membership.
4. Keep the contract narrow enough for later milestones to reuse without renaming fields.
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

Defined the minimum scope contract and explicit watch membership boundary.

What was done:

- set the scope contract to `scope_type`, `scope_id`, and `as_of`
- fixed deterministic membership rules for `asset`, `portfolio`, and `watch`
- chose the smallest durable watch boundary as `WatchScope` plus `WatchMembership`
- kept watch membership explicit, auditable, and separate from portfolio holdings

Open follow-ups:

- confirm whether the implementation milestone should reuse the same `WatchScope` name in backend models or map to an existing watchlist primitive if one appears during code scan

## Open Follow-Ups

- default to one named default watch scope for the first release unless the code scan shows multiple named sets are almost free
