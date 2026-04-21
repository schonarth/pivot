---
name: decision-locking
description: Resolve open decisions in prerequisite documents before scaffolding or implementation. Use when dependency docs still contain unresolved questions that block progress.
---

# Decision Locking

Use this skill when a milestone or implementation depends on document(s) that still contain open questions or unresolved choices.

## Start Here

- Read the dependency documents first.
- Identify every open decision that blocks progress.
- If none exist, return to the parent workflow.
- If any exist, stop and collect the decisions from the user one at a time before proceeding.

## Workflow

1. Scan the dependency documents for open questions, ambiguous choices, unresolved tradeoffs, or inconsistent statements.
2. Summarize the open decisions briefly.
3. Tell the user there are still open questions.
4. Ask for one decision at a time.
5. Record the chosen decision in the dependency document or the scaffolded docs, as appropriate.
6. Re-scan until no blocking open decisions remain.
7. Resume the parent workflow only after the dependency set is closed.

## Rules

- Do not scaffold or implement while required dependency decisions remain open.
- Keep the open-question list short and concrete.
- Ask one decision at a time when user input is needed.
- Prefer the narrowest decision that unblocks the milestone.
- If a dependency document is internally inconsistent, resolve the inconsistency before continuing.
