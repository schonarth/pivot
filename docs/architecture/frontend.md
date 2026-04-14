---
name: Frontend Architecture
description: Vue 3/Vite frontend structure and conventions
type: reference
---

# Frontend Architecture

## Stack

- Vue 3 + Vite
- TypeScript
- Pinia for state management

## Key Locations

- **Pinia stores**: `auth`, `portfolios`, `markets` in `src/stores/`
- **API base**: `${VITE_API_URL}/api` (dev proxied via Vite to `http://backend:8000`)
- **Utilities**: `src/utils/numbers.ts` for parsing numeric input
- **Path alias**: `@` → `src/`

## Important Conventions

- **Numeric input**: always use `parseNumericInput()` from `src/utils/numbers.ts` for user-entered currency/quantity (handles BR comma vs US dot decimal)
- **Route params**: always use `props: true` in route config **and** `useRoute()` fallback to handle undefined values

## Testing

- Unit tests: Vitest + Vue Test Utils
- E2E tests: Playwright from `frontend/e2e/`

## ESLint Note

`npm run lint` uses `--ext` flag incompatible with ESLint 9. Lint config may need flat config migration.
