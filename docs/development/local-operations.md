# Local Operations

## Market Simulation

```bash
./simulate_price.sh SYMBOL PRICE
./simulate_market.sh
./simulate_market.sh BR
./simulate_market.sh PETR4 VALE3
./simulate_market.sh --trends AAPL MSFT
```

`simulate_market.sh` runs indefinitely. It uses mostly small normal-distribution fluctuations of about ±0.3%, with occasional larger moves, and throttles updates from 1–60 seconds per symbol based on asset count. `--trends` adds a persistent per-asset directional bias. Use it to exercise alerts and portfolio updates while markets are closed.

## Docker Compose Watch

`develop.watch` uses `sync+restart` for `./backend`. The frontend syncs `src/`, `index.html`, and `vite.config.ts`, and rebuilds on `package.json` changes.

Watch mode targets the Dockerfile `build` stage and runs `npm run dev -- --host 0.0.0.0`, so Vite serves the frontend rather than nginx.

### Production Frontend

To run the production nginx build without HMR:

1. Remove `target: build` and `command` from the frontend service in `docker-compose.yml`.
2. Remove the frontend `develop.watch` block.
3. Remove the `./frontend/src` volume mount.
4. Run `docker compose up --build frontend`.

### Vite HMR

For true Vite HMR, configure:

```ts
server: {
  hmr: { host: 'localhost', port: 3000 },
}
```

Keep the Docker port mapping `3000:3000`, target `http://backend:8000` from the in-container Vite proxy, and ensure the Dockerfile stage includes dependencies. The current `build` stage runs `npm install` and `npm run build`; the dev-server command overrides the latter but still rebuilds a production bundle unnecessarily. A separate development stage would avoid that work.

## Database Migrations

- Initial migrations are checked in for every model app.
- `realtime` and `config` have no migrations because they have no models.
- Backend startup runs `python manage.py migrate` and idempotent `python manage.py seed_assets`.

See [data safety](data-safety.md) before any operation that can change persistent data.
