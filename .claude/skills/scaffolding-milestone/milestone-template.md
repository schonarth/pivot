# Milestone Template

Use this template for milestone coordination files and implementation task files. Keep the file small enough for one agent to execute in a single context window.

## Recommended Minimal Template

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

## Date Started

YYYY-MM-DD

## Date Completed

YYYY-MM-DD

## Branch

feat/autonomous/01-asset-context

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

## Implementation Task Expansion

Add these sections when the task needs more detail:

- `Background`
- `Detailed Requirements`
- `Proposed Approach`
- `Validation Scenarios`
- `Required Prior References`

## Required Sections

Each task spec should include, at minimum:

1. `Purpose`
2. `Roadmap Milestone`
3. `Governing ADR`
4. `Status`
5. `Owner`
6. `Date Started`
7. `Date Completed`
8. `Branch`
9. `Dependencies`
10. `Likely Files Touched`
11. `Entry Conditions`
12. `Task Steps`
13. `Tests to Add or Update`
14. `Commands to Run`
15. `Exit Conditions`
16. `Implementation Notes / What Was Done`
17. `Open Follow-Ups`

Implementation task files should usually include the additional sections above when they depend on prior findings or need clearer boundaries.
