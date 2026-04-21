# Execution Flow

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
