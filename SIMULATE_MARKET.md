# Market Simulation Guide

This guide covers the price simulation tools for testing the paper trader when markets are closed.

## Overview

Two simulators are available:

1. **Single Price Updates** — manually set a specific asset price (one-off)
2. **Continuous Market Simulator** — auto-discover assets and apply realistic random fluctuations (loops indefinitely)

Both run inside Docker and can be invoked from the project root.

## Single Price Updates

Update a specific asset to a specific price immediately. Useful for spot-testing alerts or position P&L changes.

### Usage

**Linux/Mac:**
```bash
./simulate_price.sh SYMBOL PRICE
```

**Windows:**
```batch
simulate_price.bat SYMBOL PRICE
```

### Examples

Set Apple to $150:
```bash
./simulate_price.sh AAPL 150.00
```

Set Petrobras (BR market) to 25.50 BRL:
```bash
./simulate_price.sh PETR4 25.50
```

## Continuous Market Simulator

Run an infinite loop of realistic price fluctuations (±1% per update) across a set of assets. Each symbol sleeps 1–60 seconds between updates depending on total symbol count (feels realistic even for single assets).

### Usage

Three input modes:

**Discover all seeded assets across all markets:**

Linux/Mac:
```bash
./simulate_market.sh
```

Windows:
```batch
simulate_market.bat
```

**Discover seeded assets in a specific market (BR, US, UK, or EU):**

Linux/Mac:
```bash
./simulate_market.sh BR
```

Windows:
```batch
simulate_market.bat BR
```

**Simulate specific symbols repeatedly:**

Linux/Mac:
```bash
./simulate_market.sh PETR4 VALE3 WEGE3
```

Windows:
```batch
simulate_market.bat PETR4 VALE3 WEGE3
```

## What Happens

When you run the market simulator:

1. **Discovers symbols** — queries the database for seeded assets (auto-discovery) or uses the symbols you provided
2. **Fetches latest prices** — reads from Redis cache or AssetQuote history
3. **Applies fluctuations** — multiplies each price by a random factor between 0.99 and 1.01 (±1%)
4. **Updates the system** — calls `simulate_price` for each asset, triggering:
   - Redis cache update
   - New AssetQuote database row
   - Alert evaluation (price conditions may trigger auto-trades)
   - WebSocket events (real-time portfolio updates, price notifications)
5. **Throttles** — sleeps between symbols to feel realistic:
   - 1 symbol = ~60 sec sleep
   - 10 symbols = ~6 sec each
   - 60+ symbols = ~1 sec each
6. **Loops indefinitely** — repeats from step 2 until you stop it

## Stopping the Simulator

Press `ctrl + C` to interrupt and exit.

## Examples

### Scenario 1: Test Alerts on BR Market (Market Closed)

Market is closed. You have active price alerts on Brazilian assets. Run:

Linux/Mac:
```bash
./simulate_market.sh BR
```

Watch the portfolio dashboard in real-time. Prices fluctuate, alerts trigger, portfolio value updates via WebSocket.

### Scenario 2: Stress-Test Single Asset

You want to test P&L calculations for a specific stock. Run:

Linux/Mac:
```bash
./simulate_market.sh AAPL
```

Prices swing ±1% every ~60 seconds. Watch position P&L update in real-time.

### Scenario 3: Quick Manual Test

Set a specific price for a quick check:

Linux/Mac:
```bash
./simulate_price.sh AAPL 200.00
```

Alerts evaluate immediately; portfolio updates; no loop or sleep.

## Tips

- **Docker required**: Both tools run inside the container. Ensure `docker compose` is running.
- **Seeded assets only**: Simulator only discovers assets marked `is_seeded=True` in the database. Add them via `python manage.py seed_assets` if needed.
- **No price history**: If an asset has no price in cache or database, it's skipped with a warning.
- **Real-time viewing**: Open the dashboard in your browser (`http://localhost:3000`) while the simulator runs to see live updates.
- **Multiple terminals**: Run the continuous simulator in one terminal and use `simulate_price.sh` in another for manual spot-checks.

## Troubleshooting

**"Asset not found"** — symbol doesn't exist or isn't seeded. Check via Django shell or database.

**"No symbols to simulate"** — no seeded assets in the specified market. Run `python manage.py seed_assets` first.

**WebSocket updates not showing** — ensure WebSocket connection is active in your browser (check DevTools Network tab for `/ws/portfolio/`).

**Docker container not found** — ensure `docker compose up` is running in another terminal.
