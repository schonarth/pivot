# AGENTS.md

## Project Overview

Monorepo: `backend/` (Django/DRF) + `frontend/` (Vue 3/Vite). Docker Compose orchestrates everything.

## Project Rules

- Prefer Serena's semantic code tools when Serena is available, especially for codebase exploration, symbol lookup, and targeted edits; if Serena is unavailable, continue normally with standard repo tools.
- Use `.claude/skills/milestone-lifecycle/SKILL.md` for all milestone work: scaffolding a new milestone, executing tasks from a `00 - milestone coordination.md` file, or preparing a milestone for UAT.
- Use `.claude/skills/creating-pr/SKILL.md` whenever creating a PR.
- Read the applicable references below before changing related code.

## Documentation Map

| Topic | Reference |
|---|---|
| Commands, test requirements, and Docker | [Development commands and verification](docs/development/commands-and-verification.md) |
| Simulation, Docker Compose watch, and migrations | [Local operations](docs/development/local-operations.md) |
| Destructive database-operation authorization | [Data safety](docs/development/data-safety.md) |
| Backend and frontend conventions | [Backend conventions](docs/architecture/backend.md), [Frontend architecture](docs/architecture/frontend.md) |
| Architectural invariants and supported markets | [Constraints](docs/architecture/constraints.md), [Markets](docs/architecture/markets.md) |
| Simulated price-data design | [Simulated price data](docs/architecture/simulated-price-data.md) |
| Known bug patterns | [Known bug patterns](docs/troubleshooting/known-bugs.md) |
| API endpoints and field conventions | [API reference](docs/reference/api.md) |
| Full documentation index | [docs/README.md](docs/README.md) |
