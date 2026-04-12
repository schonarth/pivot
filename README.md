# Pivot <img src="./frontend/public/pivot-logo.png" alt="Pivot Logo" style="float: left; width: 20px; margin: 0 20px 20px 0;" />

**A paper trading simulator** for learning investment strategies, testing alerts, and experimenting with portfolio management across global markets without risking real capital.



---

## Overview

Pivot is a full-stack web application that lets you:

- **Paper trade** across multiple markets: Brazil (BRL), US (USD), UK (GBP), and Europe (EUR)
- **Set price alerts** with optional auto-trading triggers
- **Simulate market prices** when markets are closed for testing
- **Track portfolio performance** with time-weighted returns
- **Monitor real-time updates** via WebSocket

Perfect for developing trading strategies, testing alert logic, and learning portfolio management in a risk-free environment.

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.10+ (for backend development)

### Running the Application

**With Docker (recommended):**

```bash
docker compose up --watch
```

This starts:
- Frontend on `http://localhost:3000` (Vite dev server with hot reload)
- Backend on `http://localhost:8000` (Django API)
- Redis (Celery broker + cache)
- PostgreSQL (database)

**Without Docker:**

Backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_assets
python manage.py runserver
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

### First Login

1. Create a superuser: `python manage.py createsuperuser`
2. Navigate to `http://localhost:3000`
3. Register or login with your credentials
4. Create your first portfolio and start trading

---

## Features

### Portfolios

- Create multiple portfolios for different markets
- Track cash balance, invested value, and unrealized P&L
- View historical snapshots and time-weighted returns (TWR)
- Deposit/withdraw funds

### Trading

- Execute buy/sell orders with automatic fee calculation
- Track positions with average cost, current price, and unrealized P&L
- Browse market listings and asset history
- Fee structure varies by market

### Price Alerts

- Set price thresholds (above/below)
- Optional notifications when triggered
- Optional auto-trading on alert conditions
- Auto-trade sizing: fixed quantity or percentage-based
- Track alert history and trigger outcomes

### Market Simulation

When markets are closed, use the simulator to test alerts and portfolio behavior:

#### Single Price Update

Update a specific asset price immediately:

**Linux/Mac:**
```bash
./simulate_price.sh SYMBOL PRICE
```

**Windows:**
```batch
simulate_price.bat SYMBOL PRICE
```

**Example:**
```bash
./simulate_price.sh AAPL 150.00
```

#### Continuous Market Simulator

Run an infinite loop of realistic price fluctuations:

**Discover all seeded assets:**
```bash
./simulate_market.sh
```

**Specific market (BR, US, UK, EU):**
```bash
./simulate_market.sh BR
```

**Specific symbols:**
```bash
./simulate_market.sh PETR4 VALE3 WEGE3
```

**With directional trends:**
```bash
./simulate_market.sh --trends BR
./simulate_market.sh --trends AAPL MSFT
```

#### How the Simulator Works

1. **Discovers symbols** — queries seeded assets or uses symbols you provide
2. **Fetches latest prices** — reads from Redis cache or database
3. **Applies fluctuations** — uses normal distribution for realistic movements
   - Most updates: ±0.3% (realistic calm market)
   - Some updates: ±1–2% (occasional larger swings)
4. **Updates the system** — triggers:
   - Redis cache updates
   - Database quote records
   - Alert evaluation (auto-trades may execute)
   - WebSocket events (real-time portfolio updates)
5. **Throttles realistically** — sleep time depends on symbol count
6. **Loops indefinitely** — press `Ctrl+C` to stop

#### Examples

**Test alerts on Brazilian market:**
```bash
./simulate_market.sh BR
```

**Stress-test a single stock:**
```bash
./simulate_market.sh AAPL
```

**Manually set a price for quick testing:**
```bash
./simulate_price.sh AAPL 200.00
```

#### Tips

- Seeded assets only: run `python manage.py seed_assets` first
- Watch the dashboard in real-time while simulator runs
- Run the continuous simulator in one terminal; use `simulate_price.sh` in another for spot-checks
- With `--trends`, the same assets get the same directional bias (deterministic/reproducible)

#### Troubleshooting

- **"Asset not found"** — symbol doesn't exist or isn't seeded
- **"No symbols to simulate"** — no seeded assets in the market; run `python manage.py seed_assets`
- **WebSocket updates not showing** — check DevTools Network tab for `/ws/portfolio/` connection
- **Docker container not found** — ensure `docker compose up` is running

---

## Architecture

### Frontend (Vue 3 + TypeScript)

- **Framework:** Vue 3 with Vite
- **State management:** Pinia stores
- **Real-time:** WebSocket via `ws/portfolio/`
- **Styling:** CSS custom properties (light/dark mode ready)
- **Type safety:** Full TypeScript with type inference

**Run dev server:**
```bash
npm run dev
```

**Lint & type-check:**
```bash
npm run lint
npm run typecheck
```

**Production build:**
```bash
npm run build
```

### Backend (Django + REST Framework)

- **Framework:** Django 5.2 with Django REST Framework
- **Real-time:** Django Channels + Redis
- **Task queue:** Celery + Redis
- **Database:** PostgreSQL
- **Authentication:** JWT (15 min access, 7 day refresh)

**Migrations:**
```bash
python manage.py migrate
```

**Seed initial data:**
```bash
python manage.py seed_assets
```

**Run tests:**
```bash
pytest
```

**Lint & type-check:**
```bash
ruff check .
ruff check --fix .
```

---

## Markets Supported

| Market | Currency | Fee | Exchange |
|--------|----------|-----|----------|
| BR | BRL | 0.03% | BVMF |
| US | USD | 0% | XNYS |
| UK | GBP | 0.1% | XLON |
| EU | EUR | 0.1% | XPAR |

---

## Development

### Project Structure

```
backend/          # Django API
frontend/         # Vue 3 frontend
docker-compose.yml # Multi-container setup
```

### Key Commands

**Backend:**
```bash
python manage.py migrate           # Apply database migrations
python manage.py seed_assets       # Seed market data
ruff check .                       # Lint
ruff check --fix .                 # Lint + fix
pytest                             # Run tests
```

**Frontend:**
```bash
npm run typecheck   # Type-check (required before commit)
npm run lint        # ESLint
npm run build       # Production build
```

**Docker:**
```bash
docker compose up --watch          # Dev mode with hot reload
docker compose up                  # Production mode
docker compose build --no-cache    # Rebuild images
```

---

## Environment Variables

Backend (`backend/.env`):
```
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@db:5432/pivot
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
```

Frontend (`.env.local` or `vite.config.ts`):
```
VITE_API_URL=http://localhost:8000
```

---

## Troubleshooting

### WebSocket Connection Issues

- Ensure `/ws/portfolio/` connection is active (DevTools → Network)
- Check `realtime` consumer logs: `docker compose logs realtime`
- Verify Redis is running: `docker compose logs redis`

### Authentication Failures

- JWT access token expires after 15 min; refresh automatically via `axios` interceptor
- Check `localStorage` for `access_token` and `refresh_token`
- Invalid refresh token → logout and re-login

### Database Errors

- Run migrations: `python manage.py migrate`
- Check PostgreSQL logs: `docker compose logs db`

### Simulator Not Working

- Ensure seeded assets exist: `python manage.py seed_assets`
- Verify Docker container is running: `docker compose up`
- Check for port conflicts (default: 3000, 8000, 5432, 6379)

---

## API Documentation

Available at `http://localhost:8000/api/` when backend is running.

Key endpoints:
- `POST /api/accounts/register/` — Register new user
- `POST /api/accounts/login/` — Login & get JWT tokens
- `GET /api/portfolios/` — List user's portfolios
- `POST /api/portfolios/` — Create portfolio
- `GET /api/portfolios/{id}/summary/` — Portfolio summary
- `POST /api/trading/execute-buy/` — Execute buy order
- `POST /api/trading/execute-sell/` — Execute sell order
- `GET /api/alerts/` — List portfolio alerts
- `POST /api/alerts/` — Create alert
- `WS /ws/portfolio/` — Real-time WebSocket updates

---

## License

Private project. See LICENSE file for details.

---

## Contributing

See `CLAUDE.md` and `AGENTS.md` for development guidelines.

For issues or questions, refer to the project docs or open an issue.

---

**Built with ❤️ for learning and experimentation.**
