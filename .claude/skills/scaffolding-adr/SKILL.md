---
name: scaffolding-adr
description: Create a short, well-formed ADR capturing the core architectural decision for an approved SPEC. Use when a SPEC is approved and needs its governing ADR extracted or written.
---

# Scaffolding ADR

Use this skill when an approved SPEC needs a corresponding architectural decision record.

## When to Use

- A SPEC has been approved but has no governing ADR yet
- A significant architectural choice (technology, pattern, boundary) was made and needs a permanent record
- You need to extract the core decision from a SPEC's "Resolved Decisions" section

## What Belongs in an ADR (and what doesn't)

**ADR content:**
- The problem that forced a choice (1-2 sentences)
- The specific choice made and the primary reason for it (1-2 sentences)
- The key tradeoffs or consequences (3-5 bullets)

**Not ADR content:**
- Functional requirements → those belong in the SPEC
- Detailed constraints or budgets → those belong in the SPEC's "Resolved Decisions"
- Implementation steps → those belong in milestone task files

## Placement

New ADR files live in:

```
docs/adrs/ADR-00X-<short-decision-name>.md
```

ADR numbers mirror SPEC numbers: ADR-001 governs SPEC-001, ADR-002 governs SPEC-002, etc.

## After Writing

- Link the ADR from the SPEC's `Governing ADR:` field
- Link the SPEC from the ADR's `SPEC:` field
- Keep the ADR short: 15-25 lines of content max

## Read the Template

- [ADR Template](adr-template.md)
