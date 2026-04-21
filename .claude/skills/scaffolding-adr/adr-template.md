# ADR Template

Use this template when creating a new ADR. Keep it short — 15-25 lines of content. The SPEC holds the detail; the ADR records the decision.

```md
---
name: <Short decision name>
description: <One-line description of the architectural decision>
type: reference
---

# ADR-00X: <Decision title — phrase as a choice, e.g. "Deterministic X Over LLM-Driven Y">

Status: Accepted
Date: YYYY-MM-DD
SPEC: [SPEC-00X-<short-name>](../specs/SPEC-00X-<short-name>.md)

## Context

<1-2 sentences: what problem forced a choice? What would go wrong without a decision?>

## Decision

<1-2 sentences: what was chosen and the key reason. Be specific about what was rejected in favor of what.>

## Consequences

- <tradeoff or benefit 1>
- <tradeoff or benefit 2>
- <tradeoff or benefit 3>
```

## What makes a good ADR title

Good: "Deterministic Context Selection Over LLM-Driven Retrieval"
Good: "Bounded Continuity Layer, Not a Durable Narrative Engine"
Bad: "Context selection approach" (too vague)
Bad: "Use deterministic ranking with bucket caps of 0-2 and a hard prompt budget of 12 items" (too specific — that's a Resolved Decision in the SPEC)

## Status vocabulary

- `Draft` — written but not yet reviewed
- `Accepted` — approved and governing the SPEC
- `Superseded` — replaced by a later ADR (add a `Superseded by: ADR-00X` line)
