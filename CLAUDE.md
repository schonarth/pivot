# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **Architecture & reference**: See `docs/architecture/` and `AGENTS.md` for complete system documentation.

## Commands

### Backend (`backend/` — inside container or local venv)

```bash
python manage.py migrate
python manage.py seed_assets          # idempotent; seed market configs + assets
ruff check .                          # lint
ruff check --fix .                    # lint + auto-fix
pytest                                # all tests
pytest path/to/test_file.py::TestClass::test_method   # single test
pytest -k "test_name_pattern"         # filter by name
```

### Frontend (`frontend/`)

```bash
npm run typecheck   # vue-tsc --noEmit — REQUIRED before considering frontend work done
npm run lint        # ESLint
npm run build       # typecheck + production build (same as Docker build runs)
```

**Testing the frontend**: don't use the Preview pane, as Docker prevents access. Use Playwright at `http://localhost:3000/`

### Docker

```bash
docker compose up --watch             # dev mode; file watching + Vite dev server in container
docker compose up                     # production build (nginx serves frontend)
docker compose build --no-cache frontend
```

## Quick Reference

- **Architecture details**: `docs/architecture/` (apps, core loop, constraints, auth, websockets, frontend, markets)
- **Known bugs**: `docs/troubleshooting/known-bugs.md`
- **Solved problems**: `docs/solutions/` — search by keyword or issue ID
- **Full reference**: `AGENTS.md` for complete commands, architecture, and testing procedures
