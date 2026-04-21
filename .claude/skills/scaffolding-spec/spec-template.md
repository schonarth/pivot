# SPEC Template

Use this template when creating a new SPEC file. Fill in every section. Leave `Resolved Decisions` empty until decisions are locked.

```md
---
name: <Short human-readable name>
description: Spec for <one-line description of what this milestone does>
type: reference
---

# SPEC

## SPEC-00X <Title>

Status: Draft
Governing ADR: [ADR-00X-<short-name>](../adrs/ADR-00X-<short-name>.md)  _(omit if no new architectural decision was made)_

## Roadmap Position

This SPEC corresponds to Milestone X of the <Roadmap Name> roadmap:

- [<Roadmap Name>](../roadmaps/<roadmap-folder>/roadmap.md)

Its role is narrow: <one sentence describing the specific capability this milestone adds>.

It is not intended to <list 2-3 things explicitly out of scope>.

## Context

<2-4 sentences: what gap or user need does this milestone address? Reference earlier SPECs by number if relevant.>

## Decision

<2-4 sentences: what approach was chosen and why? This should be the high-level shape of the solution.>

## Intended Shape

<Describe the expected implementation shape: what new step or layer is added, where it fits in the existing pipeline, and what it produces.>

## Resolved Decisions

<Add sub-sections here as decisions are locked. Each sub-section: heading = the decision, body = the rationale and constraints.>

## Constraints

- <key constraint 1>
- <key constraint 2>

## Non-Goals

- <explicit non-goal 1>
- <explicit non-goal 2>

## Notes

This SPEC should remain independently mergeable and user-releaseable when implemented.

Expected user-facing value:
- <one sentence: what the user gets when this milestone ships>
```
