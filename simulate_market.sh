#!/usr/bin/env bash
# Market simulator shortcut: applies random ±1% price fluctuations to assets.
# Usage:
#   ./simulate_market.sh              # discover all seeded assets, all markets
#   ./simulate_market.sh BR           # discover seeded assets in BR market
#   ./simulate_market.sh PETR4 VALE3  # simulate specific symbols repeatedly
# Runs indefinitely until interrupted (Ctrl+C). Throttles realistically (~1–60 sec per symbol).
set -euo pipefail
docker compose exec backend bash scripts/simulate_market.sh "$@"
