# Development Commands and Verification

## Backend

Run inside `backend/`, a backend container, or a local virtual environment.

```bash
python manage.py migrate
python manage.py seed_assets
python manage.py runserver
ruff check .
ruff check --fix .
pytest
```

`runserver` is not used in Docker.

## Frontend

Run from `frontend/`.

```bash
npm install
npm run dev
npm run build
npm run typecheck
npm run lint
```

Always run `npm run typecheck` before considering frontend work done. The Docker build runs `vue-tsc --noEmit`; type errors break the container build.

`npm run lint` uses an `--ext` flag incompatible with ESLint 9 and requires a flat-config migration.

## Tests

Always run relevant tests before considering work done. Fix the underlying software issue or update tests only when requirements have changed.

### Backend

```bash
pytest
pytest alerts/test_views.py -v
docker compose exec backend pytest
```

Use `docker compose exec backend pytest` in Docker. All backend tests must pass (currently 70/70 across accounts, alerts, markets, portfolios, and trading). Fixtures in `conftest.py` provide `authenticated_client` and model factories. Mock `realtime.services.publish_event` in tests that trigger async events.

### Frontend

```bash
npm run test
npm run test:ui
npx playwright test
npx playwright test --headed
```

Unit tests use Vitest and Vue Test Utils; current setup issues include Pinia initialization and Vue Router routing. E2E tests live in `frontend/e2e/`, should cover complete journeys, and currently have configuration issues that must be resolved before a feature is complete.

### Completion Checks

1. Run backend tests: `docker compose exec backend pytest`.
2. Run frontend typecheck: `npm run typecheck`.
3. Run frontend unit tests: `npm run test`.
4. Run frontend E2E tests: `npx playwright test`.
5. Before stopping a running backend after substantial work or test runs, check `/api/system/query-stats` for N+1 or query-heavy signals.

## Docker

```bash
docker compose up
docker compose up --watch
docker compose watch
docker compose build --no-cache frontend
```
