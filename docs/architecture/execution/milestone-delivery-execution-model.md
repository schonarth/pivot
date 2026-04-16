---
name: Milestone Delivery Execution Model
description: Reusable execution guide for large-scope milestone-based work
type: reference
---

# Milestone Delivery Execution Model

Status: Approved

## Purpose

Define how large-scope work should be executed when a roadmap is broken into milestones, ADRs, and small implementation specs.

This document is reusable across roadmap-driven efforts. It is not specific to one feature area.

## Core Principles

- keep milestone scope explicit
- keep task scope small enough for one agent to complete in one context window
- prefer sequential, auditable progress over large opaque implementation bursts
- require quick project scanning before implementation to avoid duplication
- require explicit handoff from earlier milestone outputs when later milestones depend on them
- require tests and verification before tasks are considered done
- require each task agent to update its own task file with status, owner (use model name), dates, and what was done before it marks the task complete
- make UAT as smooth as possible by catching major issues before handoff

## Milestone Folders

Execution artifacts should live under:

- `docs/architecture/roadmaps/<roadmap-folder>/milestones/`

Folder naming rule:

- one folder per milestone
- prefix with milestone number for ordering
- use the milestone name in plain language

Examples:

- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/01 - asset-context-expansion`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/02 - temporal-narrative-continuity`

Creation rule:

- milestone `00` folder may be created immediately when the roadmap is accepted
- every later milestone folder should be created only after that milestone's ADR is approved

Roadmap numbering rule:

- roadmap numbers are global within `docs/architecture/roadmaps/`
- milestone numbers are local to each roadmap
- ADR numbers remain global within `docs/architecture/adrs/`

## Branching

All development should happen on milestone branches using:

- `feat/autonomous/[milestone-number]-[short-name]`

Examples:

- `feat/autonomous/00-baseline`
- `feat/autonomous/01-asset-context`

## Spec Files

Each milestone folder should contain small, sequential spec files.

Rationale:

- keep each task small enough for one agent to execute independently
- reduce context-window bloat
- make execution easy to audit, resume, and hand off

Structure rules:

- the first file coordinates milestone execution
- later files cover one small task or a tightly related task group
- a file may contain more than one task only when those tasks are tightly correlated
- each file should stay small enough for one agent to execute in a single context window

Clarification:

- coordination files should stay relatively light and operational
- implementation task files should be mini-specs, not just tickets
- the goal is not verbosity for its own sake, but enough specificity that one agent can execute confidently without re-deriving requirements from the whole roadmap
- the orchestrator should normally execute `00 - milestone coordination.md` itself
- the orchestrator should normally delegate execution of task files `01+` to agents
- delegation is primarily about keeping each agent's context window small and focused
- every milestone `00 - milestone coordination.md` file should explicitly require reading:
  - the roadmap the milestone belongs to
  - this milestone delivery execution model
- when a milestone depends on outputs from an earlier milestone, the coordination file should name the exact earlier files that must be read and treated as normative inputs
- dependent task files should repeat those earlier-file dependencies when the handoff materially affects boundaries, vocabulary, interfaces, or storage decisions

Naming rule:

- two-digit numeric prefix

Examples:

- `00 - milestone coordination.md`
- `01 - define context boundaries.md`
- `02 - deduplication and ranking.md`

## Spec File Template

Each task spec should include, at minimum:

1. `Purpose`
2. `Roadmap Milestone`
3. `Governing ADR`
4. `Status`
5. `Owner`
6. `Branch`
7. `Dependencies`
8. `Likely Files Touched`
9. `Entry Conditions`
10. `Task Steps`
11. `Tests to Add or Update`
12. `Commands to Run`
13. `Exit Conditions`
14. `Implementation Notes / What Was Done`
15. `Open Follow-Ups`

Implementation task files should usually include these additional sections:

16. `Background`
17. `Detailed Requirements`
18. `Proposed Approach`
19. `Validation Scenarios`
20. `Required Prior References` when the task depends on earlier milestone findings

Completion rule:

- a task is not complete until the task file itself has been updated to reflect the work actually done
- the agent completing the task should set `Status`, `Owner`, `Date Started`, `Date Completed`, and `Implementation Notes / What Was Done` before handing off
- this update is part of the task, not a separate cleanup step

Use judgment:

- coordination files: lighter, execution-focused
- implementation files: spec-heavy
- final validation or release files: checklist-heavy plus validation detail

Recommended minimal template:

```md
# 01 - Example Task

## Purpose

Short description of the task outcome.

## Roadmap Milestone

Milestone 1 - Asset Context Expansion

## Governing ADR

ADR-001 Open News Context Expansion

## Status

planned

## Owner

unassigned

## Branch

feat/autonomous/1-asset-context

## Dependencies

- 00 - milestone coordination.md

## Likely Files Touched

- backend/example.py
- backend/tests/test_example.py

## Entry Conditions

- ADR approved
- prerequisite task complete

## Task Steps

1. Review the requirement and expected behavior.
2. Quickly scan the project for overlapping features or existing implementation patterns.
3. Implement the smallest correct change.
4. Add or update tests.
5. Run verification commands.

## Tests to Add or Update

- smoke tests for happy path
- unit tests for discovered edge cases

## Commands to Run

- lint
- typecheck
- affected unit tests

## Exit Conditions

- behavior implemented
- tests passing
- no relevant regressions
- spec updated with actual outcome

## Implementation Notes / What Was Done

Short note describing what was actually implemented, especially if it differs from the plan.

## Open Follow-Ups

- none
```

Recommended implementation-task expansion:

```md
## Background

Why this task exists, what earlier decision it depends on, and what later task it unblocks.

## Detailed Requirements

- required behaviors
- explicit non-behaviors
- constraints and invariants

## Proposed Approach

- likely reuse points in the repo
- expected implementation shape
- what not to invent

## Validation Scenarios

- happy path examples
- important edge cases
- regression risks to check

## Required Prior References

- earlier ADRs, milestone task files, or baseline documents that must be read before implementation
- only include when the task depends on prior findings materially enough that omission would risk architectural drift
```

## Cross-Milestone Handoff Rule

When Milestone `N` depends on Milestone `N-1` or another earlier milestone:

- the milestone coordination file must list the exact earlier files to review
- entry conditions must say those files are not only complete, but read and adopted as working constraints
- early task files should explicitly restate the required prior references when they affect insertion points, interface contracts, shared vocabulary, or storage boundaries
- later implementation tasks should verify that the new behavior still respects those inherited constraints instead of re-deriving them from scratch

## Coordination File Rule

Every milestone `00 - milestone coordination.md` file should make these startup requirements explicit:

- read the roadmap the milestone belongs to in full before executing milestone tasks
- read this execution model in full before executing milestone tasks
- if the milestone depends on earlier milestone outputs, read those named files before task execution as well

This should appear in the coordination file's entry conditions or task steps, not remain implicit.

## Status Model

Allowed task statuses:

- `planned`
- `in_progress`
- `blocked`
- `done`

Status meanings:

- `planned`: defined but not started
- `in_progress`: actively being implemented
- `blocked`: cannot proceed without clarification, prerequisite, or architectural decision
- `done`: implementation complete and all required verification passed

## Ownership

Each task spec should record:

- current owner or `unassigned`
- working branch
- date started
- date completed

The goal is accountability and traceability, not bureaucracy.

## Agent Execution Rule

Each agent should begin by:

1. understanding what the task requires
2. quickly scanning the project for previously implemented features, overlapping behavior, and existing patterns

This scan is required to avoid duplicate implementations and to keep work aligned with the current architecture.

Sub-agents are used primarily to keep context windows small, not merely to parallelize work.

Default execution model:

- orchestrator owns milestone coordination, sequencing, progress reporting, and UAT handoff
- delegated agents own execution of the numbered task files after `00`
- if one agent must handle multiple task files, it should still work through them sequentially with narrow context

## Testing Policy

### Per-Task Minimum

Each independently testable unit must have at least smoke coverage:

- happy path at minimum
- edge cases added as they are discovered

Each task must also include:

- writing or updating tests where appropriate
- running the affected tests
- running lint
- running typecheck

A task is not done until:

- required tests pass
- lint passes
- typecheck passes
- relevant existing tests still pass

### Milestone-End Verification

At the end of each milestone:

- integration tests are required
- integration tests should verify backend and frontend meet correctly
- smoke tests must have been run already during task execution

## Blocker and Escalation Rule

If an agent finds:

- an architectural conflict
- an ambiguous requirement
- a missing prerequisite
- evidence that the requested behavior overlaps with existing functionality in a risky way

Then the agent should:

1. stop implementation
2. mark the task `blocked`
3. describe the blocker briefly and concretely
4. escalate to the orchestrator
5. avoid inventing new scope to work around the problem

## Progress Tracking

The orchestrator should:

- report progress continuously
- update task files after implementation is complete
- make incremental commits as significant tasks land
- report in for UAT at the end of each milestone

## Implementation Notes Rule

The `Implementation Notes / What Was Done` section should be:

- slightly more detailed than a commit message
- focused on what was actually done, not the original plan
- as short as possible while still capturing meaningful changes

Example:

- planned: apples, bananas, tomatoes
- actual: apples, bananas, peanuts

The goal is to record execution drift without writing a long retrospective.

## UAT Readiness

Before reporting a milestone for UAT, all of the following should be true:

- milestone behavior is demoable
- milestone docs are updated
- obvious bugs have already been found and fixed
- smoke tests have been run
- integration tests have been run
- no known major issues remain open in the milestone scope
- known limitations are listed clearly

UAT should be as smooth as possible. Major problems should already have been found during implementation and unit/integration testing.
