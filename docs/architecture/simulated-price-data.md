# Simulated Price Data

When price histories are retained in the MLP phase, `AssetQuote` must distinguish simulated data from real market data, for example with `is_simulated=True`. During market hours, a scheduled Celery task should delete or exclude simulated entries so historical charts and analytics remain accurate. Simulated entries exist only for offline development and testing.

## Portfolio Simulation Safety

- `simulate_market.sh` applies random price fluctuations (documented as up to ±1%) indefinitely; `simulate_price.sh` applies manual overrides.
- Both create `AssetQuote` records with `is_override=True`.
- Alerts use overridden prices only when the portfolio has `is_simulating=True`.
- Real portfolios default to `is_simulating=False` and are protected from simulated auto-trades.

Use a dedicated simulation portfolio, turn on `is_simulating`, then run a simulator. Before real-market tracking or trades, confirm simulation mode is off and no orange simulation tint is visible.
