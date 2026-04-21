# Documentation Index

Organized reference for paper-trader architecture, troubleshooting, and solved problems.

## Architecture

Reference documentation for system design and implementation details.

- **[Autonomous Market Intelligence Roadmap](architecture/roadmaps/00%20-%20autonomous-market-intelligence/roadmap.md)** — Phased path from richer context to autonomous paper trading
- **[Milestone Delivery Execution Model](architecture/execution/milestone-delivery-execution-model.md)** — Reusable operating model for milestone-based large-scope implementation
- **[SPECs](../docs/specs/)** — Functional specs governing each roadmap milestone (`docs/specs/`)
- **[ADRs](../docs/adrs/)** — Architectural decision records extracted from SPECs (`docs/adrs/`)
- **[Apps](architecture/apps.md)** — Purpose of each Django app
- **[Core Event Loop](architecture/core-event-loop.md)** — Primary async cycle
- **[Constraints](architecture/constraints.md)** — Critical architectural invariants
- **[Auth](architecture/auth.md)** — JWT tokens and access control
- **[WebSocket](architecture/websocket.md)** — Real-time updates via Channels
- **[Frontend](architecture/frontend.md)** — Vue 3/Vite structure and conventions
- **[Markets](architecture/markets.md)** — Supported markets and configurations

## Troubleshooting

Diagnostics and solutions for known issues.

- **[Known Bug Patterns](troubleshooting/known-bugs.md)** — Real bugs to avoid

## Solutions

Documented fixes for problems encountered during development.

- **[AI Budget Accounting for Non-OpenAI Providers](solutions/ai-budget-accounting-non-openai-providers.md)** — Issue #001: Fix zero-cost bug for Anthropic and Google

## Reference

Historical requirements and specifications documenting the vision and implementation details.

- **[PRD — Paper Trader](reference/prd-paper-trader.md)** — Product requirements roadmap and business context
- **[PRD — MLP Phase](reference/prd-mlp.md)** — Machine Learning Phase specification: AI insights, backtesting, technical analysis
- **[Specification](reference/specification.md)** — MVP implementation specification with architecture, APIs, and data models

## Quick Links

- **Commands**: See `AGENTS.md` for full command reference
- **Lean reference**: `CLAUDE.md` for Claude Code-specific guidance
- **To-do tracking**: `todos/` directory with pending and resolved issues
