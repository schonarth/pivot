@echo off
REM Market simulator shortcut: applies random ±1%% price fluctuations to assets.
REM Usage:
REM   simulate_market.bat              :: discover all seeded assets, all markets
REM   simulate_market.bat BR           :: discover seeded assets in BR market
REM   simulate_market.bat PETR4 VALE3  :: simulate specific symbols repeatedly
REM Runs indefinitely until interrupted (Ctrl+C). Throttles realistically (~1-60 sec per symbol).
docker compose exec backend bash scripts/simulate_market.sh %*
