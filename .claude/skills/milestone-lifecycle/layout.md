# Layout

## Milestone Folders

Execution artifacts should live under:

- `docs/architecture/roadmaps/<roadmap-folder>/milestones/`

Folder naming rule:

- one folder per milestone
- prefix with milestone number for ordering
- use the milestone name in plain language

Examples:

- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/00 - baseline-and-interfaces`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/01 - asset-context-expansion`
- `docs/architecture/roadmaps/00 - autonomous-market-intelligence/milestones/02 - temporal-narrative-continuity`

Creation rule:

- milestone `00` folder may be created immediately when the roadmap is accepted
- every later milestone folder should be created only after that milestone's SPEC is approved

Roadmap numbering rule:

- roadmap numbers are global within `docs/architecture/roadmaps/`
- milestone numbers are local to each roadmap
- SPEC numbers remain global within `docs/specs/`
- ADR numbers remain global within `docs/adrs/`

## Branching

Create or switch to the milestone branch before scaffolding files.

All development should happen on milestone branches using:

- `feat/autonomous/[milestone-number]-[short-name]`

Examples:

- `feat/autonomous/00-baseline`
- `feat/autonomous/01-asset-context`

Milestones always branch off of `develop`.
If the branch does not exist, create it from `develop` before scaffolding begins.

## Spec Files

Each milestone folder should contain small, sequential spec files.

Rationale:

- keep each task small enough for one agent to execute independently
- reduce context-window bloat
- make execution easy to audit, resume, and hand off

Structure rules:

- the first file coordinates milestone execution
- later files cover one small task or a tightly related task group
- a file may contain more than one task only when those tasks are tightly correlated
- each file should stay small enough for one agent to execute in a single context window

Naming rule:

- two-digit numeric prefix

Examples:

- `00 - milestone coordination.md`
- `01 - define context boundaries.md`
- `02 - deduplication and ranking.md`

Coordination files should stay relatively light and operational.
Implementation task files should be mini-specs, not just tickets.
