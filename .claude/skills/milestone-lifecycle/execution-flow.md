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

## Delegated Execution

When this execution flow is invoked to execute a milestone, the user authorizes sub-agent delegation for that milestone. No additional delegation confirmation is required.

Numbered task files are the default execution units. The coordinator may provide one or more task files to `multitasking`, which determines safe sequential or parallel workstreams. Splitting a numbered task requires clear, disjoint boundaries.

Sub-agents must retain small contexts. `multitasking` owns delegation details, including workstream coordination, ownership, contracts, reasoning effort, and reconciliation. Where observable behavior is defined, each implementation workstream uses `tdd`.

## Progress Tracking

The orchestrator should:

- report user-facing progress continuously at meaningful milestones
- update task files after implementation is complete
- reconcile and verify integrated work before making incremental commits as significant tasks land
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
