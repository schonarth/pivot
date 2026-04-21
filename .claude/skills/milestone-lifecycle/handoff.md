# Handoff

## Cross-Milestone Handoff Rule

When Milestone `N` depends on Milestone `N-1` or another earlier milestone:

- the milestone coordination file must list the exact earlier files to review
- entry conditions must say those files are not only complete, but read and adopted as working constraints
- if those files still contain open decisions, stop and use [Decision Locking](../decision-locking/SKILL.md) before scaffolding or implementation continues
- early task files should explicitly restate the required prior references when they affect insertion points, interface contracts, shared vocabulary, or storage boundaries
- later implementation tasks should verify that the new behavior still respects those inherited constraints instead of re-deriving them from scratch

## Coordination File Rule

Every milestone `00 - milestone coordination.md` file should make these startup requirements explicit:

- read the roadmap the milestone belongs to in full before executing milestone tasks
- read this execution model in full before executing milestone tasks
- if the milestone depends on earlier milestone outputs, read those named files before task execution as well

This should appear in the coordination file's entry conditions or task steps, not remain implicit.

If the milestone depends on files that still have open questions, the coordination file should direct the agent to resolve them first via the decision-locking skill.

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
