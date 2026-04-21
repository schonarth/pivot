---
name: scaffolding-spec
description: Create a new SPEC file for a roadmap milestone following the SDD template. Use when a milestone has been accepted but no SPEC file exists yet.
---

# Scaffolding Spec

Use this skill when creating a new SPEC for a new or upcoming roadmap milestone.

## When to Use

- A milestone appears in the roadmap but has no SPEC file yet
- A new feature or capability needs a spec before milestone planning can start
- You need to draft a SPEC to present for approval before implementation begins

## Start Here

- Check the roadmap to confirm the milestone number and position
- Read the [SPEC Template](spec-template.md) before writing anything
- Confirm the next available SPEC number by listing `docs/specs/`

## Placement

New SPEC files live in:

```
docs/specs/SPEC-00X-<short-name>.md
```

SPEC numbers are global across all roadmaps. Check `docs/specs/` to find the next number.

## After Writing

- Set `Status: Draft` until reviewed
- Once approved, update to `Status: Approved`. If the milestone involves a new architectural decision, create an ADR using the `scaffolding-adr` skill — not every SPEC requires one
- Then scaffold the milestone folder using the `milestone-lifecycle` skill

## Source

Mirrors the SDD structure established in `docs/architecture/execution/milestone-delivery-execution-model.md`.
