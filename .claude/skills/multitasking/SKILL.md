---
name: multitasking
description: Coordinate authorized parallel work across multiple subagents with explicit ownership, shared boundary contracts, test-first integration, controlled reasoning effort, and post-implementation reconciliation. Use when a task can benefit from concurrent workstreams, especially when agents will touch connected modules, APIs, schemas, UI flows, persistence, or other cross-boundary behavior.
---

# Multitasking

Coordinate parallel execution without allowing independently correct workstreams to produce an incompatible system.

## Confirm Parallelism

1. Confirm that the user authorized subagent delegation.
2. Identify the dependency graph, critical path, and work that can proceed independently.
3. Keep immediate blockers and tightly coupled decisions with the coordinator.
4. Delegate only work that materially advances the task while the coordinator performs non-overlapping work.
5. Prefer fewer clear workstreams over maximum concurrency.

Do not delegate duplicate investigations or work whose next step depends immediately on the result.

## Lock Boundaries Before Delegating

Define and share one boundary contract before implementation begins. Include every applicable item:

- Public API routes, methods, status codes, request and response shapes.
- DTO, schema, event, database, and serialization field names and types.
- Authentication, authorization, validation, and error semantics.
- Pagination, sorting, filtering, state ownership, and lifecycle behavior.
- Shared fixtures, identifiers, defaults, and test data.
- User-visible behavior spanning multiple workstreams.

Resolve disagreements before delegation. Treat the contract as the source of truth. Change it only through an explicit coordinator decision communicated to every affected agent.

Write shared contract, integration, or end-to-end tests before implementation whenever feasible. Give those tests a single owner with a non-overlapping write scope. Share the tests, fixtures, commands, and acceptance criteria with every consumer and producer.

## Divide Ownership

Split work by coherent responsibility, not automatically by frontend and backend. Assign disjoint write sets and identify read-only dependencies.

Each delegated prompt must state:

- Goal and observable completion criteria.
- Owned files, modules, or responsibility.
- Files and interfaces that are read-only.
- The locked boundary contract.
- Shared and local tests to satisfy.
- Commands required for verification.
- Constraints, established patterns, and prohibited changes.
- Required final report, including changed paths, tests run, and blockers.
- That other agents are working concurrently and their changes must not be reverted.

Assign shared files to one owner. Route requested shared-file changes through that owner or the coordinator.

## Control Reasoning Cost

Start every subagent at the lowest practical reasoning effort, below the coordinator's effort when supported.

When an agent is blocked:

1. Require a concise blocker report with attempted approaches and concrete evidence.
2. Confirm that the problem is not a missing contract decision or coordinator-owned blocker.
3. Increase reasoning only for that agent and bounded problem, one level at a time.
4. Return the agent to its previous lower effort after the obstacle is resolved.

Do not increase effort globally or permanently because one workstream is difficult.

## Coordinate Execution

- Continue meaningful, non-overlapping coordinator work while agents run.
- Reuse an existing agent for closely related follow-up work.
- Communicate contract changes immediately to every affected workstream.
- Avoid redoing delegated work; review and integrate its result instead.
- Check progress at meaningful milestones rather than repeatedly polling.
- Stop or redirect work when new information invalidates its boundary.

## Reconcile The System

After delegated work returns:

1. Inspect repository status and every affected diff.
2. Compare implemented interfaces with the locked contract.
3. Run shared contract, integration, and end-to-end tests first.
4. Run affected unit tests, then lint, typecheck, and build checks.
5. Perform browser or live workflow verification when behavior is user-facing.
6. Fix the root contract or implementation mismatch instead of adding compensating adapters on both sides.
7. Remove dead integration code and confirm no temporary process remains.

Do not accept isolated green suites as proof of integration.

## Prevent Common Failures

Actively check for:

- Producers and consumers using different names, shapes, defaults, or status codes.
- Shared tests owned by nobody or written only after implementation.
- Overlapping write scopes and accidental reversions.
- Integration deferred until all local implementations are complete.
- Agents reporting progress without delivering verified artifacts.
- High reasoning effort used where a bounded low-effort task is sufficient.

## Combine With TDD

When `$tdd` is also active:

- Use this skill to define ownership, shared contracts, and cross-boundary tests.
- Write and confirm the shared failing tests before delegation when feasible.
- Require each agent to use `$tdd` for the behavior inside its owned scope.
- Re-run shared tests during reconciliation before accepting local green suites.

Either skill may be used independently.
