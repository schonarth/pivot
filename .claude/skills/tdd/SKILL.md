---
name: tdd
description: Implement features, bug fixes, and behavior-preserving refactors with predictable, verifiable outputs through test-driven development. Use when observable behavior and acceptance criteria are sufficiently defined to drive a red-green-refactor loop across unit, integration, contract, or end-to-end tests. Do not impose this workflow on exploratory research, spikes, or proofs of concept whose intended output is still unknown.
---

# Test-Driven Development

Drive implementation from observable behavior. Keep each cycle small, prove the failure, make the minimum change, and refactor only while green.

## Establish The Contract

Before changing production code:

1. State the observable outcome and acceptance criteria.
2. List representative examples, edge cases, permissions, and failure modes.
3. Identify the smallest vertical behavior slice.
4. Select the narrowest test level that can prove it.
5. Identify the focused test command and the broader affected suite.
6. Run the relevant baseline when existing failures could obscure the result.

If the intended output cannot yet be stated, explore or clarify first. Convert discoveries into acceptance criteria before starting TDD.

## Choose The Test Level

- Use unit tests for pure logic and behavior contained within one unit.
- Use integration tests for persistence, framework wiring, migrations, and component collaboration.
- Use contract tests for producer-consumer interfaces, schemas, and wire representations.
- Use end-to-end tests for a small number of critical user workflows.
- Use a regression test first when fixing a reported bug.

Prefer the lowest level that proves the requirement without hiding the real boundary. Add higher-level coverage when risk crosses modules or systems.

## Run Red-Green-Refactor

Repeat one behavior at a time.

### Red

1. Write one test expressing externally observable behavior.
2. Run that exact test.
3. Confirm it fails for the intended missing or incorrect behavior.
4. Fix test setup first if the failure is unrelated to the requirement.
5. Preserve concise evidence of the expected failure.

Never count a test that errors, never executes the target behavior, or fails for an unrelated reason as a valid red state.

### Green

1. Make the smallest production change that satisfies the failing example.
2. Avoid speculative abstractions and unrelated cleanup.
3. Run the focused test until it passes.
4. Run directly affected tests before adding the next example.

Do not weaken assertions merely to obtain green.

### Refactor

1. Refactor only while all affected tests are green.
2. Remove duplication, clarify names, and improve boundaries without changing behavior.
3. Keep refactoring separate from adding the next behavior.
4. Re-run the focused and affected suites after each meaningful change.

## Write Trustworthy Tests

Tests must be deterministic, isolated, repeatable, readable, and behavior-focused.

- Assert public outcomes rather than private methods or incidental implementation.
- Mock only owned boundaries or costly and uncontrollable external systems.
- Do not mock the behavior being tested.
- Avoid tautological tests that reproduce production logic.
- Keep fixtures minimal and make relevant differences visible.
- Control time, randomness, concurrency, and external state.
- Give each test one clear behavioral reason to fail.
- Prefer tests that remain valid through internal refactoring.

## Complete The Work

Before handoff:

1. Map every acceptance criterion to test evidence.
2. Run focused tests and the full relevant suite.
3. Run applicable lint, typecheck, and build commands.
4. Verify the real browser or user workflow when behavior is visual or interactive.
5. Report the confirmed red failure, green verification, and any residual test gap.

A passing suite without a previously confirmed relevant failure does not demonstrate a complete TDD cycle.

## Combine With Multitasking

When `$multitasking` is also active:

- Define shared contract, integration, and end-to-end tests before delegation whenever feasible.
- Give shared tests one owner and make them available to every workstream.
- Use this skill independently inside each agent's owned scope.
- Treat cross-boundary test failures as integration defects, even when local suites pass.

Either skill may be used independently.
