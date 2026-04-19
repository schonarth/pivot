# Product Requirements Document (PRD)
## Autonomous Paper Trading Platform with AI-Powered Market Intelligence

**Version:** 1.0
**Date:** April 8, 2026
**Author:** Gus Schonarth
**Status:** Approved for Development

---

## 1. Executive Summary

### 1.1 Product Vision
An intelligent paper trading platform that helps users practice, learn, and refine strategies across global markets without financial risk. The MVP focuses on a reliable self-hosted paper-trading loop: multi-market portfolios, manual trades, delayed price refresh, deposits/withdrawals, and price alerts with optional auto-trade. MLP extends the platform with technical analysis, MCP integration, and AI-powered intelligence.

### 1.2 Core Value Proposition
- **Multi-Market Support:** Trade paper portfolios across Brazil, USA, UK, and European markets simultaneously
- **Price-Driven Automation:** Configure price alerts that can optionally execute simple paper trades automatically
- **AI-Assisted Intelligence:** Extend the platform with LLM-powered filtering and analysis in MLP
- **Agent Integration:** MCP server allows AI assistants to manage portfolios through conversational interfaces in MLP
- **Local-First Architecture:** Run the core platform entirely via Docker with optional external integrations for market data, symbol mapping, email, and future AI features

### 1.3 Success Criteria
- **MVP (8 weeks):** User can manage multi-market paper portfolios, execute paper trades, adjust balances, refresh delayed prices, and use price alerts with optional auto-trade
- **6 months:** 100+ GitHub stars, 50+ active self-hosted instances
- **12 months:** Community contributions (strategies, indicators), optional SaaS tier launched

---

## 2. Target Audience

### 2.1 Primary Personas

**Persona 1: The Learning Trader**
- Profile: Developers/tech professionals learning to trade
- Goals: Practice strategies without losing real money, understand market mechanics
- Pain Points: Existing platforms are either too simple (no real features) or too expensive (Bloomberg Terminal)
- Technical Level: Comfortable with Docker, can run command-line tools

**Persona 2: The Algorithm Developer**
- Profile: Quantitative traders testing automated strategies
- Goals: Backtest and forward-test algorithms in realistic conditions
- Pain Points: Paid platforms don't allow custom strategy code, free platforms lack data quality
- Technical Level: Python/JavaScript developers, familiar with APIs

**Persona 3: The AI-Augmented Trader**
- Profile: Users with personal AI assistants (Claude, GPT, OpenClaw) for productivity
- Goals: Integrate trading into existing AI workflow, conversational portfolio management
- Pain Points: No trading platforms expose programmatic APIs for AI agents
- Technical Level: Power users, familiar with MCP/AI tools

### 2.2 Secondary Personas
- Portfolio managers teaching students
- Financial bloggers demonstrating strategies
- Developers building trading tools (using this as infrastructure)

---

## 3. Product Requirements

### 3.1 Core Features (MVP - 8 weeks)

**MVP Architectural Decision: Lightweight Domain Events**
- MVP includes a lightweight internal event-publication layer for key domain actions: `price_refreshed`, `alert_triggered`, `trade_executed`, and `cash_transaction_created`
- Core business logic must stay in explicit service-layer functions and Celery tasks, not in implicit signal handlers
- Events are published after successful core actions so secondary concerns can subscribe without coupling themselves into the execution path
- Intended MVP subscribers: websocket fan-out, notifications, timeline/activity history, and future integration hooks
- This is an internal architecture choice, not a separate user-facing feature

#### 3.1.1 Multi-Market Portfolio Management
**Priority:** P0 (Blocker)

**Description:**
Users can create and manage paper trading portfolios across multiple global markets with market-specific rules.

**Requirements:**
- Support markets: Brazil (B3), USA (NYSE/NASDAQ), UK (LSE), Europe (Euronext)
- Each portfolio tracks:
  - Total equity (in base currency: BRL, USD, GBP, EUR)
  - Positions: display symbol, quantity, average cost, current price, unrealized P&L
  - Cash available
  - Realized P&L (all-time and per-trade)
  - Net external cash flows (initial funding + deposits - withdrawals)
- Users can create multiple portfolios (e.g., "Conservative BR", "Tech Stocks US")
- **MVP constraint:** Each portfolio operates in ONE market only (1 portfolio = 1 market = 1 currency). No FX conversion in MVP. A Brazil portfolio holds only Brazilian stocks in BRL, a US portfolio holds only US stocks in USD, etc.
- Portfolio performance excludes external cash flows. Deposits and withdrawals adjust cash, but not trading performance.

**Acceptance Criteria:**
- [ ] User can create portfolio with name, base currency, initial capital
- [ ] Portfolio dashboard shows: total equity, cash, invested value, trading P&L, net deposits/withdrawals
- [ ] Periodic price refresh from Yahoo Finance at a configurable interval (default: 5 minutes, options: 5/15/30/60 min) during market hours
- [ ] Portfolio page includes a manual `Refresh Prices` action that fetches fresh prices for the current portfolio
- [ ] Positions table shows: display symbol, quantity, avg cost, current price, P&L ($, %), market
- [ ] Multi-portfolio view: compare performance side-by-side

**Technical Specs:**
```sql
-- Database Schema
CREATE TABLE portfolios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    name VARCHAR(100) NOT NULL,
    market VARCHAR(10) NOT NULL,         -- BR, US, UK, EU
    base_currency VARCHAR(3) NOT NULL,  -- BRL, USD, GBP, EUR
    initial_capital DECIMAL(12,2) NOT NULL,
    current_cash DECIMAL(12,2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    figi VARCHAR(32) UNIQUE,             -- Canonical identity when available
    display_symbol VARCHAR(20) NOT NULL, -- Exchange-native symbol shown in UI: PETR4, AAPL
    provider_symbol VARCHAR(30) NOT NULL, -- Provider-specific lookup symbol: PETR4.SA, AAPL
    name VARCHAR(200),
    market VARCHAR(10) NOT NULL,         -- BR, US, UK, EU
    exchange VARCHAR(20),                -- B3, NASDAQ, LSE, EURONEXT
    currency VARCHAR(3) NOT NULL,
    sector VARCHAR(50),
    is_seeded BOOLEAN DEFAULT false,
    last_symbol_sync_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_assets_market_display_symbol ON assets(market, display_symbol);

CREATE TABLE positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID REFERENCES portfolios(id) ON DELETE CASCADE,
    asset_id UUID REFERENCES assets(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    average_cost DECIMAL(12,4) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(portfolio_id, asset_id)
);

CREATE TABLE trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID REFERENCES portfolios(id),
    asset_id UUID REFERENCES assets(id),
    action VARCHAR(10) NOT NULL CHECK (action IN ('BUY', 'SELL')),
    quantity INTEGER NOT NULL,
    price DECIMAL(12,4) NOT NULL,
    total_cost DECIMAL(12,2) NOT NULL,  -- gross value before fees on SELL, after fees on BUY
    fees DECIMAL(12,2) NOT NULL,        -- brokerage fees
    realized_pnl DECIMAL(12,2),         -- populated for SELL trades
    rationale TEXT,                     -- why this trade was made
    executed_by VARCHAR(20) DEFAULT 'manual',  -- manual, alert, autonomous, agent
    executed_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE cash_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID REFERENCES portfolios(id) ON DELETE CASCADE,
    transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('initial_funding', 'deposit', 'withdrawal')),
    amount DECIMAL(12,2) NOT NULL,
    resulting_cash DECIMAL(12,2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE portfolio_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID REFERENCES portfolios(id) ON DELETE CASCADE,
    cash DECIMAL(12,2) NOT NULL,
    positions_value DECIMAL(12,2) NOT NULL,
    total_equity DECIMAL(12,2) NOT NULL,
    captured_at TIMESTAMP DEFAULT NOW()
);
```

---

#### 3.1.2 Trade Execution Engine
**Priority:** P0 (Blocker)

**Description:**
Core logic to execute paper trades (buy/sell) with realistic fees and simple validation rules.

**Requirements:**
- Execute BUY orders:
  - Check sufficient cash in portfolio
  - Calculate total cost: (price × quantity) + fees
  - Update position (add to existing or create new)
  - Include buy-side fees in the position average cost basis
  - Deduct cash from portfolio
  - Record trade in history with timestamp and rationale (optional field - if blank, system fills with "Manual operation")
- Execute SELL orders:
  - Check sufficient quantity in position
  - Calculate proceeds: (price × quantity) - fees
  - Calculate realized P&L: proceeds - (average_cost × quantity)
  - Update/remove position
  - Add cash to portfolio
  - Record trade with P&L
- Market-specific fees only in MVP:
  - Brazil: 0.03% brokerage
  - USA: $0 brokerage (Robinhood model)
  - UK: 0.10% brokerage
  - Europe: 0.10% brokerage
- Taxes are out of scope for MVP. They are neither calculated nor deducted from cash.
- Validation rules:
  - Minimum order size (e.g., $10 equivalent)
  - No short selling in MVP (future feature)
  - Manual trades may be placed outside market hours, but the UI must show a warning and execute with the last known cached price

**Acceptance Criteria:**
- [ ] Manual trade form: select asset, action (buy/sell), quantity, add rationale (optional)
- [ ] System fetches current price from cache (< 5min old)
- [ ] Displays preview: "You will buy 20 PETR4 @ R$ 42.00 = R$ 840.00 + R$ 0.25 fees = R$ 840.25 total"
- [ ] User confirms → trade executes → portfolio updates immediately
- [ ] Trade history table shows all trades with: date, symbol, action, qty, price, P&L, rationale
- [ ] If rationale is blank, system automatically fills with "Manual operation"
- [ ] Warning messages when market closed (user can still proceed), error messages for: insufficient cash, insufficient shares, invalid quantity

**Technical Specs:**
```python
# backend/trading/engine.py
from decimal import Decimal
from django.db import transaction
from .models import Portfolio, Asset, Position, Trade
from .fees import calculate_fees

class TradingEngine:
    def __init__(self, portfolio: Portfolio):
        self.portfolio = portfolio

    @transaction.atomic
    def execute_buy(self, asset: Asset, quantity: int, price: Decimal, rationale: str = "") -> Trade:
        """Execute a BUY order"""
        # Note: Market hours validation removed from engine - handled in UI with warning dialog
        # Users can trade when market is closed (using last known price)

        # Calculate costs
        fees = calculate_fees(asset.market, price * quantity, "BUY")
        total_cost = (price * quantity) + fees

        # Check sufficient cash
        if self.portfolio.current_cash < total_cost:
            raise ValueError(f"Insufficient cash: have {self.portfolio.current_cash}, need {total_cost}")

        # Update position
        position, created = Position.objects.get_or_create(
            portfolio=self.portfolio,
            asset=asset,
            defaults={"quantity": 0, "average_cost": Decimal(0)}
        )

        # Recalculate average cost
        total_shares = position.quantity + quantity
        total_invested = (position.average_cost * position.quantity) + total_cost
        position.average_cost = total_invested / total_shares
        position.quantity = total_shares
        position.save()

        # Update portfolio cash
        self.portfolio.current_cash -= total_cost
        self.portfolio.save()

        # Record trade (fill rationale if blank)
        trade = Trade.objects.create(
            portfolio=self.portfolio,
            asset=asset,
            action="BUY",
            quantity=quantity,
            price=price,
            total_cost=total_cost,
            fees=fees,
            rationale=rationale if rationale else "Manual operation",
            executed_by="manual"
        )

        return trade

    @transaction.atomic
    def execute_sell(self, asset: Asset, quantity: int, price: Decimal, rationale: str = "") -> Trade:
        """Execute a SELL order"""
        # Note: Market hours validation removed from engine - handled in UI with warning dialog
        # Users can trade when market is closed (using last known price)

        # Check position exists
        try:
            position = Position.objects.get(portfolio=self.portfolio, asset=asset)
        except Position.DoesNotExist:
            raise ValueError(f"No position in {asset.display_symbol}")

        # Check sufficient shares
        if position.quantity < quantity:
            raise ValueError(f"Insufficient shares: have {position.quantity}, trying to sell {quantity}")

        # Calculate proceeds
        fees = calculate_fees(asset.market, price * quantity, "SELL")
        gross_proceeds = price * quantity
        net_proceeds = gross_proceeds - fees

        # Calculate realized P&L
        cost_basis = position.average_cost * quantity
        realized_pnl = net_proceeds - cost_basis

        # Update position
        position.quantity -= quantity
        if position.quantity == 0:
            position.delete()
        else:
            position.save()

        # Update portfolio cash
        self.portfolio.current_cash += net_proceeds
        self.portfolio.save()

        # Record trade (fill rationale if blank)
        trade = Trade.objects.create(
            portfolio=self.portfolio,
            asset=asset,
            action="SELL",
            quantity=quantity,
            price=price,
            total_cost=gross_proceeds,
            fees=fees,
            realized_pnl=realized_pnl,
            rationale=rationale if rationale else "Manual operation",
            executed_by="manual"
        )

        return trade
```

---

#### 3.1.3 Periodic Price Updates
**Priority:** P0 (Blocker)

**Description:**
Background service that fetches delayed prices for tracked assets from Yahoo Finance API, caches them, and updates portfolios on a periodic schedule. Manual refresh is available in price-sensitive views.

**Requirements:**
- Celery Beat scheduler runs at a configurable interval (default: 5 minutes, options: 5/15/30/60 min) during market hours
- Fetch prices for all assets referenced by active positions and active alerts (deduplicated)
- Cache prices in Redis (TTL matches configured update interval)
- Persist latest quote metadata for debugging and freshness display
- Send websocket updates to connected clients (Vue frontend)
- Respect API rate limits (Yahoo Finance: ~2000 req/hour)
- Batch requests by market (all BR assets in one request, etc.)
- Provide manual refresh actions:
  - Portfolio detail view: refresh all assets in that portfolio
  - Asset detail view: refresh only that asset

**Acceptance Criteria:**
- [ ] Celery Beat task `fetch_market_prices` runs at a configurable interval (default: 5 minutes, options: 5/15/30/60 min)
- [ ] Task only runs during market hours per timezone (BR: 10am-6pm BRT, US: 9:30am-4pm EST, etc.)
- [ ] Prices cached in Redis as `price:{asset_id}` with TTL matching configured interval
- [ ] Portfolio dashboard auto-refreshes when new prices arrive (no page reload)
- [ ] Portfolio detail page shows the timestamp of the last successful refresh
- [ ] User can click `Refresh Prices` on a portfolio page to fetch all portfolio assets immediately
- [ ] User can click `Refresh Price` on an asset detail page to fetch that asset immediately
- [ ] Admin panel shows: last price update time, number of assets tracked, API requests today

**Technical Specs:**
```python
# backend/trading/tasks.py
from celery import shared_task
from celery.utils.log import get_task_logger
import yfinance as yf
from django.core.cache import cache
from .models import Asset, Position
from .market_hours import is_market_open
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = get_task_logger(__name__)

@shared_task
def fetch_market_prices():
    """Fetch delayed prices for tracked assets"""
    channel_layer = get_channel_layer()

    # Get unique assets from positions and active alerts
    active_assets = Asset.objects.filter(
        id__in=(
            list(Position.objects.values_list('asset_id', flat=True)) +
            list(Alert.objects.filter(status='active').values_list('asset_id', flat=True))
        )
    ).distinct()

    if not active_assets:
        logger.info("No active positions, skipping price update")
        return

    # Group by market
    markets = {}
    for asset in active_assets:
        if not is_market_open(asset.market):
            continue
        markets.setdefault(asset.market, []).append(asset)

    # Fetch prices by market (batch requests)
    updated_count = 0
    for market, assets in markets.items():
        symbols = [a.provider_symbol for a in assets]
        logger.info(f"Fetching {len(symbols)} prices from {market}")

        try:
            # Yahoo Finance batch download
            data = yf.download(
                tickers=" ".join(symbols),
                period="1d",
                interval="1m",
                progress=False,
                threads=True
            )

            for asset in assets:
                try:
                    # Get last price
                    price = data['Close'][asset.provider_symbol].iloc[-1]

                    # Cache in Redis (TTL matches configured interval)
                    cache_key = f"price:{asset.id}"
                    cache.set(cache_key, float(price), timeout=settings.PRICE_UPDATE_INTERVAL)

                    # Send websocket update
                    async_to_sync(channel_layer.group_send)(
                        f"prices",
                        {
                            "type": "price.update",
                            "symbol": asset.display_symbol,
                            "price": float(price),
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )

                    updated_count += 1
                except Exception as e:
                    logger.error(f"Failed to update {asset.display_symbol}: {e}")

        except Exception as e:
            logger.error(f"Failed to fetch {market} prices: {e}")

    logger.info(f"Updated {updated_count} prices")
    return updated_count

# backend/trading/celery.py
from celery import Celery
from celery.schedules import crontab

app = Celery('trading')

app.conf.beat_schedule = {
    'fetch-prices-configurable-interval': {
        'task': 'trading.tasks.fetch_market_prices',
        'schedule': settings.PRICE_UPDATE_INTERVAL,  # Configurable: 5/15/30/60 min (default 300s)
    },
}
```

```javascript
// frontend/src/composables/usePriceStream.js
import { ref, onMounted, onUnmounted } from 'vue'

export function usePriceStream() {
  const prices = ref({})
  let socket = null

  onMounted(() => {
    // Connect to Django Channels WebSocket
    socket = new WebSocket('ws://localhost:8000/ws/prices/')

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'price.update') {
        prices.value[data.symbol] = {
          price: data.price,
          timestamp: data.timestamp
        }
      }
    }

    socket.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
  })

  onUnmounted(() => {
    if (socket) {
      socket.close()
    }
  })

  return { prices }
}
```

---

#### 3.1.4 Alert System
**Priority:** P0 (Blocker)

**Description:**
Users configure simple price alerts that trigger notifications or optional automatic trades when conditions are met.

**Requirements:**
- Alert types:
  - **Price alerts:** "Notify when PETR4 < R$ 42" or "Notify when AAPL > $180"
- Alert actions:
  - **Manual mode:** Send push notification (web) or email
  - **Auto-trade mode (MVP):** Execute pre-configured trade automatically when triggered
    - Checkbox option: "Auto-execute trade when triggered"
    - Configuration fields: BUY/SELL, quantity or percentage of capital
    - Simple if/else logic (no AI validation in MVP for auto-trade)
- Alert lifecycle:
  - Active: Being checked every price update
  - Triggered: Condition met, action taken
  - Paused: User temporarily disabled
  - Alerts are one-shot in MVP. After triggering once, they move to `triggered` until edited, re-armed, or deleted by the user.
- Users can create unlimited alerts per portfolio
- Auto-trade alerts execute only when a fresh market price update triggers them. Since scheduled price updates run during market hours, alert-driven trades also execute during market hours.

**Acceptance Criteria:**
- [ ] Alert creation form: select asset, condition type, threshold, action (notify or auto-trade)
- [ ] If auto-trade selected: additional fields for BUY/SELL, quantity/percentage
- [ ] Examples:
  - "Alert me when PETR4 falls below R$ 42"
  - "Auto-buy 20 PETR4 when price falls below R$ 42"
  - "Auto-sell 50% of VALE3 when price rises above R$ 60"
- [ ] Alert list page: shows all alerts with status (active, triggered, paused) and action type
- [ ] When alert triggers:
  - Notify mode: User sees browser notification (if permission granted)
  - Auto-trade mode: Trade executes automatically, rationale includes alert details
  - Alert marked as "triggered" with timestamp
- [ ] User can edit, pause, delete alerts

**Technical Specs:**
```sql
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID REFERENCES portfolios(id),
    asset_id UUID REFERENCES assets(id),
    condition_type VARCHAR(20) NOT NULL CHECK (condition_type IN ('price_above', 'price_below')),
    threshold DECIMAL(12,4) NOT NULL,
    action VARCHAR(20) NOT NULL,          -- notify, auto_trade
    auto_trade_side VARCHAR(10),          -- BUY, SELL (for auto_trade action)
    auto_trade_quantity INTEGER,          -- Fixed quantity (for auto_trade)
    auto_trade_pct DECIMAL(5,2),          -- Percentage of capital/position (for auto_trade)
    status VARCHAR(20) DEFAULT 'active',  -- active, triggered, paused, expired
    triggered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE alert_triggers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id UUID REFERENCES alerts(id),
    triggered_price DECIMAL(12,4),
    triggered_at TIMESTAMP DEFAULT NOW(),
    action_taken TEXT  -- "Notification sent" or "Bought 20 PETR4 @ R$ 41.50"
);
```

```python
# backend/trading/tasks.py
@shared_task
def check_alerts():
    """Check all active alerts after price updates"""
    from .models import Alert, Portfolio, Asset
    from .alerts import evaluate_alert

    active_alerts = Alert.objects.filter(status='active')

    for alert in active_alerts:
        try:
            # Get current price from cache
            price = cache.get(f"price:{alert.asset_id}")
            if not price:
                continue

            # Evaluate condition
            if evaluate_alert(alert, price):
                logger.info(f"Alert {alert.id} triggered: {alert.asset.display_symbol} @ {price}")

                # Take action
                if alert.action == "notify":
                    send_notification(alert, price)
                elif alert.action == "auto_trade":
                    # Execute trade automatically when the alert fires on a fresh market price
                    execute_auto_trade(alert, price)

                # Mark as triggered
                alert.status = 'triggered'
                alert.triggered_at = datetime.utcnow()
                alert.save()

                # Record trigger
                AlertTrigger.objects.create(
                    alert=alert,
                    triggered_price=price,
                    action_taken=f"Alert triggered: {alert.asset.display_symbol} @ {price}"
                )

        except Exception as e:
            logger.error(f"Error checking alert {alert.id}: {e}")
```

---

#### 3.1.5 Cash Management (Deposits and Withdrawals)
**Priority:** P0 (Blocker)

**Description:**
Users can add or remove fictitious cash from a portfolio to simulate new funding or withdrawals without affecting trading performance metrics.

**Requirements:**
- Deposit increases `current_cash` by the requested amount
- Withdrawal decreases `current_cash` by the requested amount, never below zero
- Every deposit and withdrawal creates a cash ledger entry
- Performance calculations exclude external cash flows

**Acceptance Criteria:**
- [ ] Portfolio page includes `Deposit` and `Withdraw` actions
- [ ] Deposit updates the cash balance immediately
- [ ] Withdrawal updates the cash balance immediately
- [ ] If withdrawal amount exceeds cash balance, system warns user and clamps the resulting cash balance to zero upon confirmation
- [ ] Cash transaction history is visible in portfolio activity/history views

**Technical Specs:**
```python
# backend/trading/cash.py
from decimal import Decimal
from django.db import transaction

@transaction.atomic
def deposit_cash(portfolio, amount: Decimal):
    portfolio.current_cash += amount
    portfolio.save(update_fields=["current_cash"])

    return CashTransaction.objects.create(
        portfolio=portfolio,
        transaction_type="deposit",
        amount=amount,
        resulting_cash=portfolio.current_cash,
    )

@transaction.atomic
def withdraw_cash(portfolio, amount: Decimal):
    actual_amount = min(amount, portfolio.current_cash)
    portfolio.current_cash -= actual_amount
    portfolio.save(update_fields=["current_cash"])

    return CashTransaction.objects.create(
        portfolio=portfolio,
        transaction_type="withdrawal",
        amount=actual_amount,
        resulting_cash=portfolio.current_cash,
    )
```

---

### 3.2 MLP Features (Immediately After MVP)

#### 3.2.1 Technical Analysis Module
**Priority:** P1 (High)

**Description:**
Calculate common technical indicators (RSI, MACD, moving averages, Bollinger Bands) for tracked assets using historical price data.

**Requirements:**
- Use `pandas-ta` or `ta-lib` library for calculations
- Store historical OHLCV (Open, High, Low, Close, Volume) data in database
- Calculate indicators daily (after market close) and on-demand (when user views asset)
- Indicators to support:
  - **RSI (Relative Strength Index):** 14-period, signals overbought (>70) or oversold (<30)
  - **MACD (Moving Average Convergence Divergence):** 12/26/9 periods, signals trend changes
  - **Moving Averages:** MA20, MA50, MA200, detect golden cross (bullish) / death cross (bearish)
  - **Bollinger Bands:** 20-period, 2 std dev, signals volatility and breakouts
  - **Volume:** Compare current volume to 20-day average (unusual activity)
- Display indicators on asset detail page with visual chart (ApexCharts)

**Acceptance Criteria:**
- [ ] Asset detail page shows candlestick chart (defaults to last 90 days, user can change timeframes: 1d, 7d, 30d, 90d, 180d, 1y, 5y)
- [ ] User can toggle indicators on/off (checkboxes: RSI, MACD, MA20/50/200, Bollinger)
- [ ] Indicators calculated automatically for assets in active portfolios (daily cron job)
- [ ] On-demand calculation: if user views asset not in portfolio, fetch historical data and calculate immediately
- [ ] Alert creation allows indicator-based conditions: "Alert when PETR4 RSI < 30"

**Technical Specs:**
```sql
CREATE TABLE ohlcv (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID REFERENCES assets(id),
    date DATE NOT NULL,
    open DECIMAL(12,4) NOT NULL,
    high DECIMAL(12,4) NOT NULL,
    low DECIMAL(12,4) NOT NULL,
    close DECIMAL(12,4) NOT NULL,
    volume BIGINT NOT NULL,
    UNIQUE(asset_id, date)
);

CREATE INDEX idx_ohlcv_asset_date ON ohlcv(asset_id, date DESC);

CREATE TABLE technical_indicators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID REFERENCES assets(id),
    date DATE NOT NULL,
    rsi_14 DECIMAL(6,2),
    macd DECIMAL(12,4),
    macd_signal DECIMAL(12,4),
    macd_histogram DECIMAL(12,4),
    ma_20 DECIMAL(12,4),
    ma_50 DECIMAL(12,4),
    ma_200 DECIMAL(12,4),
    bb_upper DECIMAL(12,4),
    bb_middle DECIMAL(12,4),
    bb_lower DECIMAL(12,4),
    volume_20d_avg BIGINT,
    calculated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(asset_id, date)
);
```

```python
# backend/trading/technical.py
import pandas as pd
import pandas_ta as ta
from .models import Asset, OHLCV, TechnicalIndicators

def calculate_indicators(asset: Asset, period_days: int = 200):
    """Calculate technical indicators for an asset"""
    # Fetch historical OHLCV data
    ohlcv_data = OHLCV.objects.filter(asset=asset).order_by('date')[:period_days]

    if len(ohlcv_data) < 50:
        raise ValueError(f"Insufficient data for {asset.display_symbol}: need 50+ days, have {len(ohlcv_data)}")

    # Convert to pandas DataFrame
    df = pd.DataFrame(list(ohlcv_data.values('date', 'open', 'high', 'low', 'close', 'volume')))
    df.set_index('date', inplace=True)

    # Calculate indicators
    df.ta.rsi(length=14, append=True)  # RSI
    df.ta.macd(fast=12, slow=26, signal=9, append=True)  # MACD
    df.ta.sma(length=20, append=True)  # MA20
    df.ta.sma(length=50, append=True)  # MA50
    df.ta.sma(length=200, append=True)  # MA200
    df.ta.bbands(length=20, std=2, append=True)  # Bollinger Bands
    df['volume_ma20'] = df['volume'].rolling(window=20).mean()

    # Save to database
    for date, row in df.iterrows():
        TechnicalIndicators.objects.update_or_create(
            asset=asset,
            date=date,
            defaults={
                'rsi_14': row.get('RSI_14'),
                'macd': row.get('MACD_12_26_9'),
                'macd_signal': row.get('MACDs_12_26_9'),
                'macd_histogram': row.get('MACDh_12_26_9'),
                'ma_20': row.get('SMA_20'),
                'ma_50': row.get('SMA_50'),
                'ma_200': row.get('SMA_200'),
                'bb_upper': row.get('BBU_20_2.0'),
                'bb_middle': row.get('BBM_20_2.0'),
                'bb_lower': row.get('BBL_20_2.0'),
                'volume_20d_avg': row.get('volume_ma20')
            }
        )

    return df
```

---

#### 3.2.2 MCP Server for Agent Integration
**Priority:** P1 (High)

**Description:**
Expose an MCP (Model Context Protocol) server that allows AI agents like Claude or OpenClaw to read portfolio data, execute trades, and manage alerts through conversational interfaces.

**Requirements:**
- Python MCP SDK server running on separate port (8001)
- Authentication via API key (user-specific, stored in database)
- Exposed resources:
  - `portfolio://current` - Current portfolio state (cash, positions, P&L)
  - `portfolio://trades` - Trade history
  - `portfolio://alerts` - Active alerts
  - `market://price/{symbol}` - Current price of an asset
- Exposed tools:
  - `execute_trade` - Buy or sell assets
  - `create_alert` - Set up new alert
  - `analyze_asset` - Get technical indicators + AI analysis
  - `generate_report` - Create custom portfolio report
- Agent can subscribe to real-time updates (prices, alert triggers)

**Acceptance Criteria:**
- [ ] MCP server starts with `docker-compose up` on port 8001
- [ ] User generates API key in settings page (UUID + secret)
- [ ] AI assistant (or any MCP client) can connect and authenticate
- [ ] Example conversation:
  - User: "AI assistant, what's my portfolio status?"
  - AI assistant reads `portfolio://current`, responds: "You have R$ 978.92 cash (100%), no positions. Total P&L: +R$ 12.40"
  - User: "PETR4 is at R$ 41, should I buy?"
  - AI assistant reads `market://price/PETR4`, calls `analyze_asset(PETR4)`, gets RSI + recent news, responds with recommendation
  - User: "Buy 20 shares with 40% of capital"
  - AI assistant calls `execute_trade(PETR4, BUY, 20, rationale="User requested after confirming PETR4 @ R$ 41")`
- [ ] MCP server logs all agent actions (audit trail)

**Technical Specs:**
```python
# backend/mcp_server/server.py
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool
from trading.models import Portfolio, Trade, Alert
from trading.engine import TradingEngine
from django.contrib.auth.models import User

server = Server("paper-trader-mcp")

@server.list_resources()
async def list_resources() -> list[Resource]:
    """List available portfolio resources"""
    return [
        Resource(
            uri="portfolio://current",
            name="Current Portfolio",
            mimeType="application/json",
            description="Current portfolio state with positions and P&L"
        ),
        Resource(
            uri="portfolio://trades",
            name="Trade History",
            mimeType="application/json",
            description="All executed trades"
        ),
        Resource(
            uri="portfolio://alerts",
            name="Active Alerts",
            mimeType="application/json",
            description="Configured alerts and their status"
        )
    ]

@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read portfolio data"""
    # Extract user from auth context (API key)
    user = get_authenticated_user()
    portfolio = Portfolio.objects.get(user=user, is_primary=True)

    if uri == "portfolio://current":
        positions = Position.objects.filter(portfolio=portfolio)
        data = {
            "cash": float(portfolio.current_cash),
            "positions": [
                {
                    "symbol": p.asset.display_symbol,
                    "quantity": p.quantity,
                    "avg_cost": float(p.average_cost),
                    "current_price": get_current_price(p.asset_id),
                    "unrealized_pnl": calculate_unrealized_pnl(p)
                }
                for p in positions
            ],
            "total_value": calculate_total_value(portfolio)
        }
        return json.dumps(data)

    elif uri == "portfolio://trades":
        trades = Trade.objects.filter(portfolio=portfolio).order_by('-executed_at')[:50]
        data = [
            {
                "date": t.executed_at.isoformat(),
                "symbol": t.asset.display_symbol,
                "action": t.action,
                "quantity": t.quantity,
                "price": float(t.price),
                "rationale": t.rationale
            }
            for t in trades
        ]
        return json.dumps(data)

    # ... other resources

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available trading tools"""
    return [
        Tool(
            name="execute_trade",
            description="Execute a paper trade (buy or sell)",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Asset symbol (e.g., PETR4, AAPL)"},
                    "action": {"type": "string", "enum": ["BUY", "SELL"]},
                    "quantity": {"type": "integer", "minimum": 1},
                    "rationale": {"type": "string", "description": "Why this trade is being made"}
                },
                "required": ["symbol", "action", "quantity"]
            }
        ),
        Tool(
            name="create_alert",
            description="Create a price or indicator alert",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "condition": {"type": "string", "description": "e.g., 'price_below', 'rsi_below'"},
                    "threshold": {"type": "number"},
                    "action": {"type": "string", "enum": ["notify", "execute_trade"]}
                },
                "required": ["symbol", "condition", "threshold", "action"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> str:
    """Execute trading tool"""
    user = get_authenticated_user()
    portfolio = Portfolio.objects.get(user=user, is_primary=True)
    engine = TradingEngine(portfolio)

    if name == "execute_trade":
        asset = Asset.objects.get(symbol=arguments["symbol"])
        price = get_current_price(asset.id)

        if arguments["action"] == "BUY":
            trade = engine.execute_buy(
                asset=asset,
                quantity=arguments["quantity"],
                price=price,
                rationale=arguments.get("rationale", "")
            )
        else:
            trade = engine.execute_sell(
                asset=asset,
                quantity=arguments["quantity"],
                price=price,
                rationale=arguments.get("rationale", "")
            )

        return json.dumps({
            "success": True,
            "trade_id": str(trade.id),
            "message": f"{arguments['action']} {arguments['quantity']} {asset.display_symbol} @ {price}"
        })

    # ... other tools

# Run server
if __name__ == "__main__":
    stdio_server(server)
```

---

### 3.3 Post-MLP Features

#### 3.2.1 AI-Powered Asset Filtering
**Priority:** P2 (Medium)
**Timeline:** Week 9-10

**Description:**
Daily AI task that scans 500+ assets across all markets and filters down to 5-10 "high-potential" opportunities based on unusual volume, news sentiment, technical divergences, and macro context.

**Technical Approach:**
- Celery task runs once daily at 6am (before markets open)
- Fetches 500+ assets from multiple markets (top volume stocks)
- Filters stage 1 (fast, no AI):
  - Volume > 2x 20-day average (unusual interest)
  - Price moved ±5% yesterday (momentum)
  - Technical signals converging (e.g., RSI < 40 + MACD crossover)
- Filters stage 2 (AI, expensive):
  - Fetch last 5 news headlines for remaining ~50 assets
  - Send to configured AI model (default: gpt-4o-mini): "Analyze these 50 stocks with news. Return top 10 with highest opportunity score (0-100) and brief rationale."
  - Cache results for 24 hours
- Display "AI Picks" section on dashboard with rationale

**Cost Estimate:**
- 50 assets × 500 tokens = 25k tokens/day
- Example with GPT-4o-mini: $0.15/1M tokens = $0.00375/day = $0.11/month per user
- Acceptable for BYOK (Bring Your Own Key) model
- Users can configure which AI model to use based on available API keys

---

#### 3.2.2 Autonomous Trading Mode
**Priority:** P2 (Medium)
**Timeline:** Week 11-12

**Description:**
Users define trading strategies (rules + AI validation) that execute automatically during market hours without manual intervention.

**Features:**
- Strategy builder UI:
  - Entry conditions: "Buy PETR4 if price < R$ 42 AND RSI < 30 AND oil < $95"
  - Position sizing: "Use 40% of available cash"
  - Exit conditions: "Sell if price > R$ 50 OR RSI > 70 OR 5% stop-loss"
  - AI validation: "Ask AI to confirm macro context is favorable before executing"
- Strategy backtesting:
  - User selects date range (e.g., last 6 months)
  - System simulates strategy with historical data
  - Shows results: total return, number of trades, win rate, max drawdown
- Live execution:
  - User enables "Autonomous Mode" for a strategy
  - Celery worker evaluates strategy at a configurable interval (default: 5 minutes, options: 5/15/30/60 min) during market hours
  - When conditions met, calls AI for validation (optional)
  - Executes trade automatically if validated
  - Logs detailed rationale: "Bought 20 PETR4 @ R$ 41.50 because: [technical signals] + [AI validation: oil prices dropped due to ceasefire, favorable entry point]"

**Safety Features:**
- Daily loss limit: Stop trading if portfolio down >5% in one day
- Maximum position size: No single position > 30% of portfolio
- Kill switch: User can instantly disable autonomous mode
- Email/push notification for every autonomous trade
- Weekly summary: "Your autonomous strategy made 3 trades this week: 2 wins, 1 loss, +2.3% total"

---

#### 3.2.3 News Feed Integration
**Priority:** P2 (Medium)
**Timeline:** Week 13-14

**Description:**
Real-time news feed filtered by assets in user's portfolio, with AI-generated summaries and sentiment analysis.

**Features:**
- News sources:
  - RSS feeds: Reuters, Bloomberg, CNBC, InfoMoney, Valor Econômico (default sources)
  - Users can manage RSS feeds: add custom sources, remove unwanted sources
  - Use existing RSS library (e.g., feedparser in Python)
  - Reddit scraping (optional): r/wallstreetbets, r/investing, r/stocks
  - Twitter/X scraping (optional): Financial influencers, company accounts
- Filtering:
  - Only show news related to assets in portfolio or watchlist
  - Sentiment analysis: AI tags news as Positive, Neutral, Negative
  - Priority scoring: "High impact" news (earnings, M&A, regulatory changes) surfaced first
- AI summaries:
  - Long articles → Configured AI model generates 2-sentence summary
  - Multiple articles on same topic → "3 sources reporting on Petrobras earnings: consensus is positive, beat expectations by 12%"
- Actionable insights:
  - "This news may impact PETR4 price. Consider reviewing your position."
  - "Positive earnings report → RSI still < 40 → Good entry point (AI confidence: 78%)"

---

#### 3.2.4 Multi-User & Collaboration
**Priority:** P3 (Low)
**Timeline:** Week 15+

**Description:**
Allow multiple users to share portfolios, compare strategies, and collaborate on trades.

**Features:**
- Team portfolios: Multiple users manage same paper portfolio (for education, competitions)
- Leaderboards: Compare P&L with other users (opt-in, anonymized)
- Strategy marketplace: Users share strategies (code + backtest results), others can clone and run
- Social features: Follow other traders, copy trades (paper only), comment on trades

---

### 3.4 Non-Functional Requirements

**Note on Timezone Handling:**
The application must detect the user's local timezone (browser timezone, not container timezone) for proper UX. Market hours, chart timestamps, and trade execution times should all display in the user's local timezone. Backend stores all timestamps in UTC.

#### 3.4.1 Performance
- API response time: < 200ms for read operations, < 500ms for trade execution
- Dashboard load time: < 2 seconds on broadband
- Periodic price refresh: new quotes visible within 5 seconds of a completed refresh task
- Support 100+ concurrent users per instance (self-hosted)

#### 3.4.2 Security
- Passwords handled by Django authentication defaults
- API keys for OpenFIGI, SMTP, and future MCP/AI integrations stored via environment variables or future encrypted settings
- HTTPS required for production deployments
- Rate limiting: 100 req/minute per user (Django REST Framework throttling)
- SQL injection prevention: Django ORM parameterized queries
- XSS prevention: Vue auto-escaping, CSP headers
- Prompt injection protection: Sanitize and validate all inputs to LLM integrations, use system prompts that instruct models to refuse harmful requests

#### 3.4.3 Scalability
- Stateless backend: Can run multiple Django instances behind load balancer
- Celery workers: Can scale horizontally (add more worker containers)
- Postgres: Supports read replicas for analytics queries
- Redis: Can use Redis Cluster for high availability

#### 3.4.4 Reliability
- Database backups: Automated daily backups (Docker volume snapshots)
- Error logging: Sentry integration for exception tracking
- Uptime monitoring: Health check endpoint (`/api/health/`)
- Graceful degradation: If Yahoo Finance API down, show last cached prices with warning

#### 3.4.5 Usability
- Mobile-responsive UI (TailwindCSS responsive breakpoints)
- Dark mode support (essential for traders!)
- Keyboard shortcuts: `N` = New trade, `A` = New alert, `/` = Search
- Accessibility: ARIA labels, keyboard navigation, screen reader support

---

## 4. Technical Architecture

### 4.1 System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         User's Machine                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                   Docker Compose                      │   │
│  │                                                        │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │   │
│  │  │   Frontend   │  │   Backend    │  │  Postgres  │ │   │
│  │  │   (Vue 3)    │  │   (Django)   │  │            │ │   │
│  │  │   Port 3000  │  │   Port 8000  │  │  Port 5432 │ │   │
│  │  └──────┬───────┘  └──────┬───────┘  └─────┬──────┘ │   │
│  │         │                 │                 │         │   │
│  │         └─────────────────┴─────────────────┘         │   │
│  │                           │                           │   │
│  │         ┌─────────────────┴──────────────────┐        │   │
│  │         │                                     │        │   │
│  │  ┌──────▼───────┐  ┌──────────────┐  ┌──────▼─────┐ │   │
│  │  │    Redis     │  │ Celery Beat  │  │   Celery   │ │   │
│  │  │ (Cache/Queue)│  │  (Scheduler) │  │   Worker   │ │   │
│  │  │  Port 6379   │  └──────────────┘  └────────────┘ │   │
│  │  └──────────────┘                                    │   │
│  │                                                        │   │
│  │  ┌──────────────────────────────────────────────┐    │   │
│  │  │   Optional MLP: MCP Server (Port 8001)       │    │   │
│  │  │       (AI Agent Integration)                 │    │   │
│  │  └──────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
                   ┌──────────────────┐
                   │  External APIs   │
                   │                  │
                   │ • Yahoo Finance  │
│ • OpenFIGI       │
│ • SMTP (optional)│
│ • OpenAI API     │
                   └──────────────────┘
```

### 4.2 Technology Stack

**Frontend:**
- Vue 3.4+ (Composition API, TypeScript)
- Vite 5.0+ (build tool)
- Pinia 2.1+ (state management)
- Vue Router 4.2+
- TailwindCSS 3.4+
- ApexCharts (financial charts)
- Headless UI (accessible components)

**Backend:**
- Python 3.11+
- Django 5.0+
- Django REST Framework 3.14+
- Django built-in authentication system
- Django Channels (WebSockets)
- Celery 5.3+ (async tasks)
- Redis 7.2+ (cache + message broker)
- PostgreSQL 16+
- yfinance (Yahoo Finance API wrapper)
- OpenFIGI API (symbol resolution + FIGI mapping, with seeded fallback data)
- Lightweight domain event publisher/subscriber layer for internal extensibility
- pandas-ta (technical analysis)
- MCP Python SDK (agent integration)

**Infrastructure:**
- Docker 24+ (tested with Docker Desktop and Orbstack)
- Docker Compose 2.20+
- Nginx (production reverse proxy)

**Development Environment:**
- Docker-first approach with hot-reload (volumes mounted, HMR enabled in Vite and Django)
- Local setup available as fallback option (see docs/local-development.md)

**DevOps:**
- GitHub Actions (CI/CD)
- Docker Hub (image registry)
- Sentry (error tracking - optional)

### 4.3 Database Schema (Complete)

```sql
-- Users and Authentication
-- Use Django's built-in auth tables from day one.
-- If a custom user model is needed, it must be introduced before the first migration.

CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(64) NOT NULL,  -- SHA256 hash
    key_prefix VARCHAR(8) NOT NULL,  -- First 8 chars for display
    name VARCHAR(100),  -- "AI Assistant Key", "Mobile App", etc.
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

-- Markets and Assets
CREATE TABLE assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    figi VARCHAR(32) UNIQUE,
    display_symbol VARCHAR(20) NOT NULL,
    provider_symbol VARCHAR(30) NOT NULL,
    name VARCHAR(200),
    market VARCHAR(10) NOT NULL,  -- BR, US, UK, EU
    exchange VARCHAR(20),         -- B3, NASDAQ, LSE, EURONEXT
    currency VARCHAR(3) NOT NULL,
    sector VARCHAR(50),
    industry VARCHAR(100),
    market_cap BIGINT,
    is_seeded BOOLEAN DEFAULT false,
    last_symbol_sync_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_assets_market_display_symbol ON assets(market, display_symbol);

-- Portfolios
CREATE TABLE portfolios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    base_currency VARCHAR(3) NOT NULL,
    initial_capital DECIMAL(12,2) NOT NULL,
    current_cash DECIMAL(12,2) NOT NULL,
    is_primary BOOLEAN DEFAULT false,  -- User's main portfolio
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_portfolios_user ON portfolios(user_id);

-- Positions
CREATE TABLE positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID REFERENCES portfolios(id) ON DELETE CASCADE,
    asset_id UUID REFERENCES assets(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    average_cost DECIMAL(12,4) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(portfolio_id, asset_id)
);

CREATE INDEX idx_positions_portfolio ON positions(portfolio_id);

-- Trades
CREATE TABLE trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID REFERENCES portfolios(id),
    asset_id UUID REFERENCES assets(id),
    action VARCHAR(10) NOT NULL CHECK (action IN ('BUY', 'SELL')),
    quantity INTEGER NOT NULL,
    price DECIMAL(12,4) NOT NULL,
    total_cost DECIMAL(12,2) NOT NULL,
    fees DECIMAL(12,2) NOT NULL,
    realized_pnl DECIMAL(12,2),  -- Only for SELL trades
    rationale TEXT,
    executed_by VARCHAR(20) DEFAULT 'manual',  -- manual, alert, autonomous, agent
    executed_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_trades_portfolio_date ON trades(portfolio_id, executed_at DESC);
CREATE INDEX idx_trades_asset ON trades(asset_id);

-- Portfolio cash flows and performance snapshots
CREATE TABLE cash_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID REFERENCES portfolios(id) ON DELETE CASCADE,
    transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('initial_funding', 'deposit', 'withdrawal')),
    amount DECIMAL(12,2) NOT NULL,
    resulting_cash DECIMAL(12,2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_cash_transactions_portfolio_date ON cash_transactions(portfolio_id, created_at DESC);

CREATE TABLE portfolio_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID REFERENCES portfolios(id) ON DELETE CASCADE,
    cash DECIMAL(12,2) NOT NULL,
    positions_value DECIMAL(12,2) NOT NULL,
    total_equity DECIMAL(12,2) NOT NULL,
    captured_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_portfolio_snapshots_portfolio_date ON portfolio_snapshots(portfolio_id, captured_at DESC);

CREATE TABLE timeline_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID REFERENCES portfolios(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_timeline_events_portfolio_date ON timeline_events(portfolio_id, created_at DESC);

-- Alerts
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID REFERENCES portfolios(id),
    asset_id UUID REFERENCES assets(id),
    condition_type VARCHAR(20) NOT NULL CHECK (condition_type IN ('price_above', 'price_below')),
    threshold DECIMAL(12,4) NOT NULL,
    action VARCHAR(20) NOT NULL,
    auto_trade_side VARCHAR(10),
    auto_trade_quantity INTEGER,
    auto_trade_pct DECIMAL(5,2),
    status VARCHAR(20) DEFAULT 'active',
    triggered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_alerts_portfolio_status ON alerts(portfolio_id, status);

CREATE TABLE alert_triggers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id UUID REFERENCES alerts(id) ON DELETE CASCADE,
    triggered_price DECIMAL(12,4),
    triggered_at TIMESTAMP DEFAULT NOW(),
    action_taken TEXT
);

-- Market Data
CREATE TABLE ohlcv (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID REFERENCES assets(id),
    date DATE NOT NULL,
    open DECIMAL(12,4) NOT NULL,
    high DECIMAL(12,4) NOT NULL,
    low DECIMAL(12,4) NOT NULL,
    close DECIMAL(12,4) NOT NULL,
    volume BIGINT NOT NULL,
    UNIQUE(asset_id, date)
);

CREATE INDEX idx_ohlcv_asset_date ON ohlcv(asset_id, date DESC);

CREATE TABLE technical_indicators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID REFERENCES assets(id),
    date DATE NOT NULL,
    rsi_14 DECIMAL(6,2),
    macd DECIMAL(12,4),
    macd_signal DECIMAL(12,4),
    macd_histogram DECIMAL(12,4),
    ma_20 DECIMAL(12,4),
    ma_50 DECIMAL(12,4),
    ma_200 DECIMAL(12,4),
    bb_upper DECIMAL(12,4),
    bb_middle DECIMAL(12,4),
    bb_lower DECIMAL(12,4),
    volume_20d_avg BIGINT,
    calculated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(asset_id, date)
);

CREATE INDEX idx_indicators_asset_date ON technical_indicators(asset_id, date DESC);

-- Trading Strategies (for autonomous mode)
CREATE TABLE strategies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID REFERENCES portfolios(id),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    entry_conditions JSONB NOT NULL,  -- Rules for when to buy
    exit_conditions JSONB NOT NULL,   -- Rules for when to sell
    position_sizing JSONB NOT NULL,   -- How much to buy (% of capital)
    use_ai_validation BOOLEAN DEFAULT true,
    is_enabled BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE strategy_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id UUID REFERENCES strategies(id),
    asset_id UUID REFERENCES assets(id),
    action VARCHAR(10),  -- BUY or SELL
    quantity INTEGER,
    price DECIMAL(12,4),
    rationale TEXT,
    ai_validation TEXT,  -- AI's analysis before executing
    executed_at TIMESTAMP DEFAULT NOW()
);

-- News and AI Analysis
CREATE TABLE news_articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    url VARCHAR(1000) UNIQUE NOT NULL,
    source VARCHAR(100),
    published_at TIMESTAMP NOT NULL,
    summary TEXT,  -- AI-generated summary
    sentiment VARCHAR(20),  -- positive, neutral, negative
    relevance_score DECIMAL(3,2),  -- 0.00 to 1.00
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE news_assets (
    news_id UUID REFERENCES news_articles(id) ON DELETE CASCADE,
    asset_id UUID REFERENCES assets(id) ON DELETE CASCADE,
    PRIMARY KEY (news_id, asset_id)
);

CREATE INDEX idx_news_published ON news_articles(published_at DESC);

-- AI Picks (daily recommendations)
CREATE TABLE ai_picks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,
    asset_id UUID REFERENCES assets(id),
    opportunity_score DECIMAL(5,2),  -- 0.00 to 100.00
    rationale TEXT,
    technical_signals JSONB,
    news_context TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(date, asset_id)
);

CREATE INDEX idx_ai_picks_date_score ON ai_picks(date DESC, opportunity_score DESC);
```

### 4.4 API Endpoints

**Authentication (MVP):**
- `POST /api/auth/register` - Create account
- `POST /api/auth/login` - Get JWT token
- `POST /api/auth/logout` - Invalidate token
- `GET /api/auth/me` - Get current user

**Portfolios:**
- `GET /api/portfolios` - List user's portfolios
- `POST /api/portfolios` - Create new portfolio
- `GET /api/portfolios/{id}` - Get portfolio details
- `PUT /api/portfolios/{id}` - Update portfolio
- `DELETE /api/portfolios/{id}` - Delete portfolio
- `GET /api/portfolios/{id}/performance` - Performance chart data
- `GET /api/portfolios/{id}/summary` - Summary stats (P&L, positions count, etc.)
- `POST /api/portfolios/{id}/refresh-prices` - Refresh prices for assets in this portfolio
- `POST /api/portfolios/{id}/deposit` - Add fictitious cash to the portfolio
- `POST /api/portfolios/{id}/withdraw` - Remove fictitious cash from the portfolio (clamped to zero)
- `GET /api/portfolios/{id}/cash-transactions` - Cash ledger history

**Positions:**
- `GET /api/portfolios/{id}/positions` - List positions
- `GET /api/portfolios/{id}/positions/{asset_id}` - Position detail with unrealized P&L

**Trades:**
- `POST /api/portfolios/{id}/trades` - Execute trade (buy/sell)
- `GET /api/portfolios/{id}/trades` - Trade history (paginated)
- `GET /api/trades/{id}` - Trade detail

**Assets:**
- `GET /api/assets` - Search assets (query params: ?q=PETR, ?market=BR)
- `GET /api/assets/{symbol}` - Asset detail
- `GET /api/assets/{symbol}/price` - Current price (cached)
- `POST /api/assets/{symbol}/refresh-price` - Refresh only this asset's price
- `GET /api/assets/{symbol}/chart` - OHLCV data for chart
- `GET /api/assets/{symbol}/indicators` - Technical indicators
- `GET /api/assets/{symbol}/news` - Recent news articles

**Alerts:**
- `GET /api/portfolios/{id}/alerts` - List alerts
- `POST /api/portfolios/{id}/alerts` - Create alert
- `PUT /api/alerts/{id}` - Update alert
- `DELETE /api/alerts/{id}` - Delete alert
- `POST /api/alerts/{id}/pause` - Pause alert
- `POST /api/alerts/{id}/resume` - Resume alert

**Strategies (Autonomous Mode):**
- `GET /api/portfolios/{id}/strategies` - List strategies
- `POST /api/portfolios/{id}/strategies` - Create strategy
- `GET /api/strategies/{id}` - Strategy detail
- `PUT /api/strategies/{id}` - Update strategy
- `POST /api/strategies/{id}/enable` - Enable autonomous execution
- `POST /api/strategies/{id}/disable` - Disable autonomous execution
- `POST /api/strategies/{id}/backtest` - Run backtest
- `GET /api/strategies/{id}/executions` - Strategy execution history

**AI Features:**
- `GET /api/ai/daily-picks` - Today's AI-recommended assets
- `POST /api/ai/analyze-asset` - Get AI analysis for specific asset
- `POST /api/ai/analyze-news` - Summarize news articles
- `python manage.py inspect_divergence` - Print deterministic short-window divergence inputs, labels, and presentation text for an asset or monitored set

**MLP / Post-MVP Authentication:**
- `POST /api/auth/api-keys` - Generate MCP API key
- `DELETE /api/auth/api-keys/{id}` - Revoke API key

**System:**
- `GET /api/health` - Health check (returns 200 OK if all services up)
- `GET /api/markets/status` - Which markets are currently open
- `GET /api/system/stats` - System stats (# tracked assets, API usage, etc.)

### 4.5 Frontend Routes

```
/                          → Dashboard (portfolio summary)
/portfolios                → Portfolio list
/portfolios/new            → Create portfolio
/portfolios/:id            → Portfolio detail
/portfolios/:id/trades     → Trade history
/portfolios/:id/trades/new → Execute trade form
/portfolios/:id/alerts     → Alert management
/portfolios/:id/strategies → Strategy management (autonomous mode)

/assets                    → Asset search / browse
/assets/:symbol            → Asset detail (chart, indicators, news)

/ai-picks                  → Daily AI recommendations

/settings                  → User settings
/settings/api-keys         → MCP API key management

/login                     → Login page
/register                  → Register page
```

---

## 5. User Stories

### 5.1 Core Workflow Stories

**Story 1: Create Portfolio and Execute First Trade**
> As a new user,
> I want to create a paper trading portfolio with initial capital,
> So that I can practice trading without financial risk.

**Acceptance Criteria:**
- User registers account with email + password
- User creates portfolio: "My BR Portfolio", BRL, R$ 10,000 initial capital
- User searches for "PETR4", views current price (R$ 48.50)
- User clicks "Buy", enters quantity (20 shares), adds rationale ("Buying the dip after ceasefire")
- System shows preview: "20 PETR4 @ R$ 48.50 = R$ 970.00 + R$ 0.29 fees = R$ 970.29 total"
- User confirms → Trade executes → Portfolio shows position: 20 PETR4 @ R$ 48.50, cash: R$ 9,029.71

---

**Story 2: Set Price Alert**
> As an active trader,
> I want to receive a notification when an asset reaches my target price,
> So that I don't miss trading opportunities.

**Acceptance Criteria:**
- User navigates to Alerts page
- User creates alert: "PETR4" / "Price falls below" / "R$ 42.00" / Action: "Notify me"
- Alert appears in active alerts list
- Later, PETR4 price drops to R$ 41.80
- Celery worker detects condition, triggers alert
- User receives browser push notification: "🚨 Alert: PETR4 fell to R$ 41.80 (target: < R$ 42.00)"
- Alert marked as "Triggered" in UI

---

**Story 3: Alert With Auto-Trade**
> As an active trader,
> I want a price alert to optionally execute a simple paper trade automatically,
> So that I can react without watching the screen continuously.

**Acceptance Criteria:**
- User navigates to Alerts page
- User creates alert: "PETR4" / "Price falls below" / "R$ 42.00" / Action: "Auto-buy 20 shares"
- Alert appears in active alerts list
- Later, a scheduled market price update detects PETR4 at R$ 41.80
- System triggers the alert and executes the BUY automatically using the last fetched price
- Trade history shows rationale like: "Auto-trade triggered by alert: price_below 42.00"
- Alert is marked as "Triggered" in UI

---

**Story 4: Manual Price Refresh**
> As a user,
> I want to manually refresh delayed prices when I am on a portfolio or asset page,
> So that I can make decisions using the freshest price the system can fetch.

**Acceptance Criteria:**
- User is viewing a portfolio with a 30-minute refresh interval configured
- User clicks `Refresh Prices`
- System fetches fresh quotes for all assets in that portfolio immediately
- Portfolio values update without page reload
- UI shows the new `Last updated at` timestamp
- User then opens PETR4 detail page and clicks `Refresh Price`
- System refreshes only PETR4 and updates the asset detail view

---

**Story 5: View Performance Without Cashflow Distortion**
> As a user,
> I want deposits and withdrawals to change my cash balance without inflating my portfolio performance,
> So that returns reflect trading results rather than added capital.

**Acceptance Criteria:**
- User starts with R$ 1,000 cash and no positions
- User deposits another R$ 1,000
- Portfolio cash becomes R$ 2,000 immediately
- Dashboard shows `Net deposits: R$ 2,000`
- Trading performance remains 0% until trades create gains or losses

---

### 5.2 MLP / Post-MVP Stories

**Story 6: View Technical Analysis**
> As a technical trader,
> I want to see RSI, MACD, and moving averages for my assets,
> So that I can make data-driven trading decisions.

**Acceptance Criteria:**
- User clicks on PETR4 position in portfolio
- Asset detail page loads with candlestick chart (last 90 days)
- User toggles "Show RSI" → RSI line appears below chart (currently 28, oversold zone)
- User toggles "Show MA20/50" → Moving averages overlay on chart (MA20 crossing above MA50 = golden cross)
- User sees indicator summary: "RSI: 28 (Oversold), MACD: Bullish crossover, MA20 > MA50 (Golden Cross)"
- User interprets: Strong buy signal

---

**Story 7: AI Assistant Executes Trade via MCP**
> As a user with an AI assistant,
> I want it to execute trades on my behalf after discussing the strategy,
> So that I can manage my portfolio conversationally.

**Acceptance Criteria:**
- User says to assistant: "PETR4 is at R$ 41.50 now. Check if it's a good entry."
- Assistant reads `market://price/PETR4` (R$ 41.50)
- Assistant calls `analyze_asset(PETR4)` → Gets RSI=28, MACD bullish, recent news: "Ceasefire extended"
- Assistant responds: "PETR4 @ R$ 41.50 is a strong buy. RSI oversold (28), MACD bullish crossover, ceasefire reduced geopolitical risk. Recommend buying 20 shares (40% capital)."
- User: "Do it."
- Assistant calls `execute_trade(PETR4, BUY, 20, rationale="AI-validated entry: oversold RSI + bullish MACD + ceasefire news")`
- MCP server executes trade → assistant confirms: "Bought 20 PETR4 @ R$ 41.50. Total cost: R$ 830.29. You now have R$ 9,199.42 cash."

---

**Story 8: Backtest Trading Strategy**
> As a quantitative trader,
> I want to backtest a strategy against historical data,
> So that I can validate it before using autonomous mode.

**Acceptance Criteria:**
- User creates strategy: "Buy PETR4 when RSI < 30 and oil < $95, sell when RSI > 70 or +10% profit"
- User clicks "Backtest" → Selects date range: Jan 1 - Mar 31, 2026
- System simulates strategy with historical OHLCV and indicator data
- Results displayed:
  - Total trades: 5 (3 wins, 2 losses)
  - Win rate: 60%
  - Total return: +8.2%
  - Max drawdown: -3.1%
  - Chart shows equity curve vs IBOV benchmark
- User satisfied → Enables autonomous mode with confidence

---

### 5.3 Edge Case Stories

**Story 9: Execute Trade During Market Closed**
> As a user,
> I should not be prevented from executing trades when the market is closed, but with a warning
> So that the simulation reflects real trading conditions.

**Acceptance Criteria:**
- User tries to buy PETR4 at 8pm BRT (B3 closed)
- Trade form displays next market open time: "Reopens tomorrow at 10:00 BRT"
- System shows confirmation dialog (not native Javascript `confirm`): "Brazil market (B3) is closed. Trading hours: 10:00-18:00 BRT. You will buy with the last known price, but the market may open with a different price [tomorrow|on Monday]. Do you want to proceed?" and only executes if the user confirms.

---

**Story 10: Insufficient Cash for Trade**
> As a user,
> I should receive a clear error if I try to buy more than I can afford,
> So that I understand my capital constraints.

**Acceptance Criteria:**
- User has R$ 1,000 cash
- User tries to buy 100 PETR4 @ R$ 48.50 = R$ 4,850 total
- System shows error: "Insufficient cash. You have R$ 1,000.00, but this trade requires R$ 4,850.29."
- Suggestion displayed: "Maximum you can buy: 20 shares (R$ 970.29)"

---

**Story 11: Deposits**
> As a user,
> I should be able to add virtual funds to my wallet,
> So that it reflects real-life scenarios.

**Acceptance Criteria:**
- User has R$ 1,000 cash
- User clicks "$/Deposit" button
- Small dialog appears with numerical input
- User enters "3000" (this is ficticious, so there is no verification)
- User's wallet is updated to R$ 4,000 immediately after confirming the dialog

---

**Story 12: Withdrawals**
> As a user,
> I should be able to remove virtual funds to my wallet (up to but not beyond zero),
> So that it reflects real-life scenarios.

**Acceptance Criteria:**
- User has R$ 1,000 cash
- User clicks "$/Withdraw" button
- Small dialog appears with numerical input
- User enters "300"
  - User's wallet is updated to R$ 700 immediately after confirming the dialog
- User enters "3000"
  - Dialog shows warning: "Entered value is greater than your balance. It will be set to zero."
  - User confirms
  - User's wallet is set to R$ 0 immediately after confirming the dialog.

---

**Story 13: AI Analysis Timeout (MLP)**
> As a user requesting AI analysis,
> I should receive a fallback response if the AI API times out,
> So that I'm not blocked from trading.

**Acceptance Criteria:**
- User clicks "AI Analysis" on PETR4
- LLM API times out after 30 seconds (configurable)
- System falls back to technical indicators only
- Message displayed: "AI analysis unavailable (API timeout). Showing technical signals only: RSI=28 (Oversold), MACD=Bullish. Consider manual review."
- User can still proceed with trade based on technical data

---

## 6. Success Metrics

### 6.1 MVP Success (8 weeks)
- [ ] 3+ GitHub stars in first week after release
- [ ] 2+ users successfully self-host and provide feedback
- [ ] Core features functional: multi-user auth, portfolios, trades, delayed prices + refresh, deposits/withdrawals, price alerts with optional auto-trade
- [ ] Zero critical bugs reported in first month

### 6.2 6-Month Goals
- [ ] 50+ GitHub stars
- [ ] 20+ active self-hosted instances (tracked via telemetry ping, opt-in)
- [ ] 5+ community contributions (PRs accepted: new strategies, indicators, bug fixes)
- [ ] Featured on ProductHunt, Hacker News (front page), r/algotrading

### 6.3 12-Month Vision
- [ ] 200+ GitHub stars
- [ ] 100+ active users
- [ ] Optional SaaS tier launched (R$ 29/month, managed hosting + AI included)
- [ ] Partnership with trading education platforms (use our tool for courses)
- [ ] Mobile app (React Native) for portfolio monitoring

---

## 7. Development Timeline

### **Phase 1: Foundation (Weeks 1-2)**
- [ ] Project setup: Docker Compose, Django + Vue scaffolding
- [ ] Database schema implementation (Postgres + migrations)
- [ ] Authentication: Register, login, JWT tokens
- [ ] Portfolio CRUD: Create, read, update, delete portfolios
- [ ] Asset model: Seed database with 100-500 popular assets (BR, US, UK, EU) including display symbols, provider symbols, and FIGI where known
- [ ] OpenFIGI integration for symbol resolution of non-seeded assets, with persistent Postgres cache

### **Phase 2: Core Trading (Weeks 3-4)**
- [ ] Trade execution engine: Buy/sell with fees and closed-market warning behavior
- [ ] Position management: Calculate unrealized P&L, average cost
- [ ] Periodic price updates: Celery + Yahoo Finance integration
- [ ] Manual portfolio-level and asset-level refresh actions
- [ ] Cash management: deposits, withdrawals, cash ledger
- [ ] Lightweight domain-event publication for prices, alerts, trades, and cash transactions
- [ ] Trade history: List, filter, export to CSV
- [ ] Dashboard UI: Portfolio summary, positions table, performance chart

### **Phase 3: Alerts & Performance (Weeks 5-6)**
- [ ] Alert system: Create, trigger, notify (browser push, optional email)
- [ ] Auto-trade alerts: execute BUY/SELL when price-above/price-below rules trigger
- [ ] Portfolio performance: snapshots + performance that excludes external cash flows
- [ ] Market hours UX: warn on manual closed-market trades, auto-trade only from market-hour price updates
- [ ] Portfolio activity/timeline: trades + cash transactions + alert triggers

### **Phase 4: Polish & Launch (Weeks 7-8)**
- [ ] UI/UX polish: Dark mode, responsive design, keyboard shortcuts
- [ ] Documentation: README, installation guide, API docs
- [ ] Demo video: 3-minute walkthrough (YouTube)
- [ ] GitHub release: v1.0.0 with Docker Compose one-command setup
- [ ] Launch: ProductHunt, Hacker News, Reddit (r/algotrading, r/selfhosted)

### **Phase 5: MLP (Weeks 9-12)**
- [ ] Technical indicators: RSI, MACD, moving averages, Bollinger Bands (daily timeframe only)
- [ ] OHLCV data: Fetch and store historical data
- [ ] Asset detail page: Candlestick chart with indicators (ApexCharts)
- [ ] MCP server: stdio transport, explicit `portfolio_id` required in each tool call
- [ ] AI asset filtering: Daily job to surface 5-10 high-potential picks

### **Phase 6: Post-MLP (Weeks 13-16)**
- [ ] Autonomous trading mode (weeks 13-14)
- [ ] Strategy backtesting (weeks 13-14)
- [ ] News feed integration (weeks 15-16)
- [ ] Collaboration and community features (weeks 15-16)

---

## 8. Risk Assessment & Mitigation

### 8.1 Technical Risks

**Risk 1: Yahoo Finance API Rate Limits**
- **Probability:** Medium
- **Impact:** High (no price updates = broken app)
- **Mitigation:**
  - Implement aggressive caching (5-minute TTL)
  - Batch requests by market (1 request for 50 symbols instead of 50 requests)
  - Fallback to secondary API (Alpha Vantage, Twelve Data)
  - Document API limits clearly: "Supports up to 500 assets per instance"

**Risk 2: AI API Costs Spiral Out of Control**
- **Probability:** Medium
- **Impact:** Medium (users complain about high costs)
- **Mitigation:**
  - BYOK (Bring Your Own Key) model: Users provide their own OpenAI/Anthropic API keys
  - Clear cost estimation in UI: "This analysis will cost ~$0.01"
  - Rate limiting: Max 10 AI requests per day for free tier
  - Configurable AI models: Users select which model to use based on available API keys (gpt-4o-mini, claude-3-5-haiku-20241022, etc.)
  - User might only have one AI provider configured - system adapts accordingly

**Risk 3: Database Performance Degrades with Scale**
- **Probability:** Low
- **Impact:** Medium (slow queries on large portfolios)
- **Mitigation:**
  - Proper indexing on all foreign keys and query paths
  - Pagination for all list endpoints (max 100 items per page)
  - Benchmark with synthetic data (1000+ trades, 100+ assets)
  - Connection pooling (Django `CONN_MAX_AGE`, pgBouncer if needed)

**Risk 4: Real-Time WebSockets Don't Scale**
- **Probability:** Low
- **Impact:** Low (price updates lag for some users)
- **Mitigation:**
  - Use Django Channels with Redis backend (proven scalable)
  - Implement WebSocket heartbeat / reconnection logic
  - Fallback to polling if WebSocket fails (every 10 seconds)
  - Document limits: "Supports 100 concurrent WebSocket connections per instance"

### 8.2 Product Risks

**Risk 5: Users Find Existing Competitors Superior**
- **Probability:** Medium
- **Impact:** High (low adoption)
- **Mitigation:**
  - Differentiate clearly: multi-market, local-first, simple automation, future MCP/AI roadmap
  - Engage early users for feedback (beta program)
  - Iterate quickly based on user pain points
  - Open-source advantage: Community can add features competitors can't

**Risk 6: Too Complex for Target Audience**
- **Probability:** Medium
- **Impact:** Medium (users abandon after setup)
- **Mitigation:**
  - One-command setup: `docker-compose up` must "just work"
  - Video tutorial (3 minutes, covers installation → first trade)
  - Default portfolio template: Pre-configured with popular assets
  - Progressive disclosure: Hide advanced features (autonomous mode, strategies) behind "Advanced" tab

**Risk 7: Legal/Regulatory Issues**
- **Probability:** Low
- **Impact:** High (forced to shut down)
- **Mitigation:**
  - Clear disclaimer: "This is a paper trading simulator. No real money is involved."
  - No financial advice: "For educational purposes only. Not investment advice."
  - Terms of Service: Users acknowledge they are responsible for own trading decisions
  - No payment processing (until SaaS tier): Self-hosted = no regulatory exposure

---

## 9. Resolved Scope Decisions

1. **MVP scope**
   - MVP is portfolios + trades + periodic prices + manual refresh + deposits/withdrawals + price alerts with simple auto-trade.
   - MCP, technical indicators, AI filtering, and news move to MLP or later.

2. **Closed-market rule**
   - Manual trades are allowed at any time, using the last known cached price when the market is closed.
   - The UI must warn when a manual trade is placed outside market hours.
   - Alert-driven auto-trades only occur from fresh market price updates, which run during market hours.

3. **Accounting model**
   - MVP uses simple paper-trading accounting: `portfolios.current_cash`, `positions`, `trades`, `cash_transactions`, and `portfolio_snapshots`.
   - Fees are included in execution and P&L.
   - Taxes are out of scope.
   - Performance excludes deposits and withdrawals.

4. **Internal event model**
   - MVP includes lightweight domain-event publication for `price_refreshed`, `alert_triggered`, `trade_executed`, and `cash_transaction_created`.
   - Core business logic remains in explicit service-layer functions and Celery tasks.
   - Event subscribers are for secondary effects only: notifications, websocket updates, timeline history, and future integrations.

5. **Price source and freshness**
   - Delayed quotes are acceptable for MVP.
   - Users choose refresh frequency.
   - Manual refresh exists on portfolio and asset views.

6. **Symbol identity**
   - Use FIGI as the canonical instrument identity when available.
   - Store `display_symbol` separately for exchange-native UI display.
   - Store `provider_symbol` separately for market-data lookups.
   - Seed major assets in Postgres to reduce OpenFIGI dependency on first run.

7. **Refresh behavior**
   - Portfolio views use portfolio-level refresh.
   - Asset detail views use asset-level refresh.

8. **User model**
   - Multi-user authentication is required from day one.
   - Use Django authentication from the start to avoid later migration pain.

9. **Notification channels**
   - Browser notifications are required in MVP.
   - Email notifications are optional when SMTP is configured.

10. **Alerts scope**
   - MVP alerts support `price_above` and `price_below` only.
   - Percentage-change and indicator-based alerts move to MLP.

---

## 10. Appendix

### 10.1 Market-Specific Configuration

```python
# backend/trading/markets.py
MARKET_CONFIG = {
    "BR": {
        "name": "Brazil (B3)",
        "timezone": "America/Sao_Paulo",
        "trading_hours": {"open": "10:00", "close": "18:00"},
        "currency": "BRL",
        "brokerage_fee_pct": 0.0003  # 0.03%
    },
    "US": {
        "name": "United States (NYSE/NASDAQ)",
        "timezone": "America/New_York",
        "trading_hours": {"open": "09:30", "close": "16:00"},
        "currency": "USD",
        "brokerage_fee_pct": 0.0  # $0 (Robinhood model)
    },
    "UK": {
        "name": "United Kingdom (LSE)",
        "timezone": "Europe/London",
        "trading_hours": {"open": "08:00", "close": "16:30"},
        "currency": "GBP",
        "brokerage_fee_pct": 0.0010  # 0.10%
    },
    "EU": {
        "name": "Europe (Euronext)",
        "timezone": "Europe/Paris",
        "trading_hours": {"open": "09:00", "close": "17:30"},
        "currency": "EUR",
        "brokerage_fee_pct": 0.0010  # 0.10%
    }
}
```

### 10.2 Symbol Resolution and Asset Seeding

- `display_symbol` is the exchange-native symbol shown to users (`PETR4`, `AAPL`, `BP`, etc.)
- `provider_symbol` is the market-data lookup symbol used with Yahoo Finance or another provider (`PETR4.SA`, `AAPL`, etc.)
- `figi` is the canonical internal identity when available
- The app ships with seeded asset rows for 100-500 major symbols across supported markets
- OpenFIGI is used to resolve and persist mappings for non-seeded assets or user-added symbols
- OpenFIGI mappings are cached in Postgres through the `assets` table so lookups survive restarts and repeated sessions

### 10.3 Lightweight Event Architecture

```python
# backend/trading/events.py
from dataclasses import dataclass
from datetime import datetime
from typing import Any

@dataclass
class DomainEvent:
    event_type: str
    portfolio_id: str
    payload: dict[str, Any]
    occurred_at: datetime


def publish_event(event: DomainEvent) -> None:
    """Publish an internal post-commit event to subscribed handlers."""
```

**MVP Event Types:**
- `price_refreshed`
- `alert_triggered`
- `trade_executed`
- `cash_transaction_created`

**Rule:** Core business logic must not depend on implicit signal handlers. Events are for secondary effects only.

### 10.4 Configuration via Docker Compose

The application is configured primarily through `docker-compose.yml` environment variables:

**Configurable Parameters:**
- `PRICE_UPDATE_INTERVAL` - Price update interval in seconds (default: 300 for 5 min, options: 300/900/1800/3600)
- `WEBSOCKET_FALLBACK_POLLING` - WebSocket polling fallback interval in seconds (default: 10)
- `FRONTEND_PORT` - Frontend port (default: 3000)
- `BACKEND_PORT` - Backend port (default: 8000)
- `MCP_PORT` - MCP server port (default: 8001)
- `OPENFIGI_API_KEY` - OpenFIGI API key (optional; raises rate limits)
- `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL` - Optional SMTP settings for email alerts
- `AI_TIMEOUT` - Timeout for AI API requests in seconds (default: 30, MLP+)
- `OPENAI_API_KEY` - OpenAI API key (optional, user-provided)
- `ANTHROPIC_API_KEY` - Anthropic API key (optional, user-provided)
- `AI_MODEL_PRIMARY` - Primary AI model ID (default: gpt-4o-mini, configurable to claude-3-5-haiku-20241022, etc.)
- `AI_MODEL_FALLBACK` - Fallback AI model if primary fails (optional)

**Note:** Position Size limits and Daily Loss Limits are configured per-portfolio in the UI, not in docker-compose.yml.

### 10.5 Docker Compose File

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: paper_trader
      POSTGRES_USER: trader
      POSTGRES_PASSWORD: changeme
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U trader"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - ./backend:/app
    ports:
      - "${BACKEND_PORT:-8000}:8000"
    environment:
      DATABASE_URL: postgresql://trader:changeme@postgres:5432/paper_trader
      REDIS_URL: redis://redis:6379/0
      DJANGO_SECRET_KEY: ${DJANGO_SECRET_KEY:-dev-secret-key-change-in-production}
      DJANGO_DEBUG: ${DJANGO_DEBUG:-True}
      PRICE_UPDATE_INTERVAL: ${PRICE_UPDATE_INTERVAL:-300}
      OPENFIGI_API_KEY: ${OPENFIGI_API_KEY:-}
      EMAIL_HOST: ${EMAIL_HOST:-}
      EMAIL_PORT: ${EMAIL_PORT:-587}
      EMAIL_HOST_USER: ${EMAIL_HOST_USER:-}
      EMAIL_HOST_PASSWORD: ${EMAIL_HOST_PASSWORD:-}
      EMAIL_USE_TLS: ${EMAIL_USE_TLS:-True}
      DEFAULT_FROM_EMAIL: ${DEFAULT_FROM_EMAIL:-noreply@paper-trader.local}
      AI_TIMEOUT: ${AI_TIMEOUT:-30}
      WEBSOCKET_FALLBACK_POLLING: ${WEBSOCKET_FALLBACK_POLLING:-10}
      OPENAI_API_KEY: ${OPENAI_API_KEY:-}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:-}
      AI_MODEL_PRIMARY: ${AI_MODEL_PRIMARY:-gpt-4o-mini}
      AI_MODEL_FALLBACK: ${AI_MODEL_FALLBACK:-}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A paper_trader worker -l info
    volumes:
      - ./backend:/app
    environment:
      DATABASE_URL: postgresql://trader:changeme@postgres:5432/paper_trader
      REDIS_URL: redis://redis:6379/0
      PRICE_UPDATE_INTERVAL: ${PRICE_UPDATE_INTERVAL:-300}
      OPENFIGI_API_KEY: ${OPENFIGI_API_KEY:-}
      AI_TIMEOUT: ${AI_TIMEOUT:-30}
      OPENAI_API_KEY: ${OPENAI_API_KEY:-}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:-}
      AI_MODEL_PRIMARY: ${AI_MODEL_PRIMARY:-gpt-4o-mini}
      AI_MODEL_FALLBACK: ${AI_MODEL_FALLBACK:-}
    depends_on:
      - postgres
      - redis

  celery_beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A paper_trader beat -l info
    volumes:
      - ./backend:/app
    environment:
      DATABASE_URL: postgresql://trader:changeme@postgres:5432/paper_trader
      REDIS_URL: redis://redis:6379/0
      PRICE_UPDATE_INTERVAL: ${PRICE_UPDATE_INTERVAL:-300}
      OPENFIGI_API_KEY: ${OPENFIGI_API_KEY:-}
    depends_on:
      - postgres
      - redis

  mcp_server:
    build:
      context: ./backend
      dockerfile: Dockerfile.mcp
    command: python mcp_server/server.py
    volumes:
      - ./backend:/app
    ports:
      - "${MCP_PORT:-8001}:8001"
    environment:
      DATABASE_URL: postgresql://trader:changeme@postgres:5432/paper_trader
      REDIS_URL: redis://redis:6379/0
      OPENAI_API_KEY: ${OPENAI_API_KEY:-}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:-}
      AI_MODEL_PRIMARY: ${AI_MODEL_PRIMARY:-gpt-4o-mini}
      AI_MODEL_FALLBACK: ${AI_MODEL_FALLBACK:-}
    depends_on:
      - postgres
      - redis

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    command: npm run dev -- --host 0.0.0.0 --port 3000
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "${FRONTEND_PORT:-3000}:3000"
    environment:
      VITE_API_URL: http://localhost:${BACKEND_PORT:-8000}
      VITE_WS_URL: ws://localhost:${BACKEND_PORT:-8000}
      VITE_WEBSOCKET_FALLBACK_POLLING: ${WEBSOCKET_FALLBACK_POLLING:-10}
    depends_on:
      - backend

volumes:
  postgres_data:
```

### 10.6 Quick Start Commands

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/paper-trader.git
cd paper-trader

# Start all services
docker-compose up -d

# Wait for services to be healthy (~30 seconds)
docker-compose ps

# Run migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Seed sample assets
docker-compose exec backend python manage.py seed_assets

# Access the app
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/api
# Django Admin: http://localhost:8000/admin
# MCP Server: post-MVP / MLP component

# View logs
docker-compose logs -f backend
docker-compose logs -f celery_worker

# Stop all services
docker-compose down

# Stop and remove volumes (reset database)
docker-compose down -v
```

---

## 11. Conclusion

This PRD defines a technically feasible paper trading platform that differentiates itself through:

1. **Multi-market support** (BR, US, UK, EU)
2. **Simple automation in MVP** (price alerts with optional auto-trade)
3. **AI-powered intelligence roadmap** (filtering, analysis, validation in MLP+)
4. **Agent integration roadmap** (MCP server for AI assistants in MLP)
5. **Local-first architecture** (Docker, optional external integrations)

The 8-week MVP timeline is aggressive but achievable with focused execution. MLP and later phases provide a clear roadmap for technical analysis, MCP, AI features, and broader ecosystem capabilities.

**Next Steps:**
1. Review and approve this PRD
2. Set up GitHub repository with project structure
3. Begin Phase 1 (Foundation) development
4. Weekly progress reviews (every Friday)
5. Launch v1.0.0 at end of Week 8

🦞 **Let's build this!**
