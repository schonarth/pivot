# Paper Trader MLP Specification

**Version:** 1.0  
**Date:** April 12, 2026  
**Author:** Gus Schonarth  
**Status:** In Development  
**Reference:** Builds on `SPEC.md` (MVP); complements `PRD-paper-trader.md` (roadmap)

---

## 1. Scope

### 1.1 MLP Scope

MLP adds **intelligence infrastructure** to the completed MVP. Three interlocking features:

1. **Technical Analysis Module**: OHLCV history + indicator calculation (RSI, MACD, MAs, Bollinger Bands)
2. **AI-Powered Insights**: Asset filtering, indicator-based recommendations, trade validation (BYOK pattern)
3. **News Integration**: Scrape + summarize recent news with AI sentiment analysis

**Delivery Timeline**: 6 weeks post-MVP

### 1.2 Design Principles

- **MVP remains unmodified**: MLP is additive; MVP views, APIs, business logic unchanged
- **BYOK (Bring Your Own Key)**: Users provide their own AI API keys; app never bears AI costs
- **Hard stops + controls**: Users set monthly AI budget with enforcement and warnings
- **Graceful degradation**: If AI unavailable, app shows technicals only; no broken UI
- **Separate backtesting**: Backtesting is its own module; don't mix with trading

### 1.3 Explicitly Out of MLP

- OAuth / live authentication broker (code ready for future plug-and-play)
- Autonomous trading strategies (requires backtesting + strategy engine; deferred to post-MLP)
- RSS feed integration (scraping first; RSS in post-MLP)
- Indicator-based alerts (MVP alerts remain price-only; indicator conditions deferred)
- Historical backtesting with multiple strategies (single-strategy, 6-month simulations only)

---

## 2. Architecture

### 2.1 New Django Apps

| App | Purpose |
|-----|---------|
| `markets` (extended) | Add OHLCV historical fetch, scrape news sources |
| `trading` (extended) | Add IndicatorCalculator service, backtesting foundation |
| `ai` | AIService abstraction, embedding auth + budget tracking |
| `backtesting` | BacktestEngine, scenario modeling, simulation results |

### 2.2 Core Data Model Additions

#### OHLCV
```python
class OHLCV(models.Model):
    asset = ForeignKey(Asset, on_delete=CASCADE)
    date = DateField()
    open = DecimalField(max_digits=12, decimal_places=4)
    high = DecimalField(max_digits=12, decimal_places=4)
    low = DecimalField(max_digits=12, decimal_places=4)
    close = DecimalField(max_digits=12, decimal_places=4)
    volume = BigIntegerField()
    
    class Meta:
        unique_together = ('asset', 'date')
        indexes = [Index(fields=['asset', '-date'])]
```

#### TechnicalIndicators
```python
class TechnicalIndicators(models.Model):
    asset = ForeignKey(Asset, on_delete=CASCADE)
    date = DateField()
    
    # RSI (14-period)
    rsi_14 = DecimalField(max_digits=6, decimal_places=2, null=True)
    
    # MACD (12/26/9)
    macd = DecimalField(max_digits=12, decimal_places=4, null=True)
    macd_signal = DecimalField(max_digits=12, decimal_places=4, null=True)
    macd_histogram = DecimalField(max_digits=12, decimal_places=4, null=True)
    
    # Simple Moving Averages
    ma_20 = DecimalField(max_digits=12, decimal_places=4, null=True)
    ma_50 = DecimalField(max_digits=12, decimal_places=4, null=True)
    ma_200 = DecimalField(max_digits=12, decimal_places=4, null=True)
    
    # Bollinger Bands (20-period, 2 std dev)
    bb_upper = DecimalField(max_digits=12, decimal_places=4, null=True)
    bb_middle = DecimalField(max_digits=12, decimal_places=4, null=True)
    bb_lower = DecimalField(max_digits=12, decimal_places=4, null=True)
    
    # Volume Analysis
    volume_20d_avg = BigIntegerField(null=True)
    
    calculated_at = DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('asset', 'date')
        indexes = [Index(fields=['asset', '-date'])]
```

#### AIAuth (User AI Configuration)
```python
class AIAuth(models.Model):
    user = ForeignKey(User, on_delete=CASCADE, unique=True)
    provider_name = CharField(choices=['openai', 'anthropic', 'other'])
    
    # BYOK: Encrypted API key
    api_key_encrypted = BinaryField(null=True)
    
    # Future OAuth: Access token
    access_token = CharField(max_length=1024, null=True)
    token_expires_at = DateTimeField(null=True)
    
    # Budget controls
    monthly_budget_usd = DecimalField(
        max_digits=8, decimal_places=2, default=10.00
    )
    alert_threshold_pct = IntegerField(default=10)  # Warn at 90% consumed
    
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

#### AIUsage (Cost Tracking)
```python
class AIUsage(models.Model):
    user = ForeignKey(User, on_delete=CASCADE)
    provider_name = CharField()
    model_name = CharField()
    
    prompt_tokens = IntegerField()
    completion_tokens = IntegerField()
    cost_usd = DecimalField(max_digits=8, decimal_places=4)
    
    feature_used = CharField(
        choices=['filtering', 'insight', 'validation', 'news']
    )
    
    timestamp = DateTimeField(auto_now_add=True)
    month = DateField()  # For aggregation (first day of month)
    
    class Meta:
        indexes = [
            Index(fields=['user', 'month']),
            Index(fields=['user', '-timestamp']),
        ]
```

### 2.3 Service Layer

#### IndicatorCalculator (`trading/technical.py`)
- `calculate_for_asset(asset, min_ohlcv_rows=200)` — Calculate all indicators for one asset
- Uses pandas-ta for calculations
- Returns DataFrame with all indicator columns

#### NewsService (`markets/news.py`)
- `fetch_recent_news(asset, days=7)` — Scrape recent news for asset
- Sources: Yahoo Finance news, Seeking Alpha snippets, MarketWatch
- Returns list of (title, url, date, source)

#### AIService (`ai/services.py`)
- Abstraction layer supporting OpenAI, Anthropic, future providers
- Methods:
  - `analyze_asset(asset, include_news=True)` — Recommendation with reasoning
  - `validate_trade(portfolio, asset, action, quantity)` — Trade approval + sizing
  - `filter_opportunities(market, num_picks=10)` — Find high-potential assets
  - `summarize_news(headlines)` — Summarize multiple news items
- Respects BYOK auth (encrypt keys, use user's API quota)
- Tracks cost; raises `BudgetExceeded` if limit reached

#### BacktestEngine (`backtesting/engine.py`)
- Replay OHLCV data sequentially
- Evaluate strategy conditions at each price point
- Track simulated trades, P&L, drawdown, win rate

---

## 3. API Specification

### 3.1 Settings Endpoints (AI Configuration)

#### POST /api/settings/ai
**Add or update user's AI configuration**

Request:
```json
{
  "provider": "openai",
  "api_key": "sk-...",
  "monthly_budget_usd": 25.00,
  "alert_threshold_pct": 10
}
```

Response:
```json
{
  "provider": "openai",
  "monthly_budget_usd": 25.00,
  "alert_threshold_pct": 10,
  "this_month_consumed_usd": 3.45
}
```

#### GET /api/settings/ai
**Retrieve user's AI configuration (key never returned)**

Response:
```json
{
  "provider": "openai",
  "monthly_budget_usd": 25.00,
  "alert_threshold_pct": 10,
  "this_month_consumed_usd": 3.45,
  "is_over_budget": false
}
```

#### DELETE /api/settings/ai
**Remove user's AI configuration (disables AI features)**

---

### 3.2 Asset Endpoints (Extended)

#### GET /api/assets/{symbol}/indicators?market=BR
**Retrieve latest technical indicators for asset**

Response:
```json
{
  "symbol": "PETR4",
  "market": "BR",
  "date": "2026-04-11",
  "indicators": {
    "rsi_14": 45.2,
    "macd": 0.0523,
    "macd_signal": 0.0445,
    "macd_histogram": 0.0078,
    "ma_20": 29.15,
    "ma_50": 28.90,
    "ma_200": 27.50,
    "bb_upper": 31.45,
    "bb_middle": 29.50,
    "bb_lower": 27.55,
    "volume_20d_avg": 2500000
  }
}
```

#### GET /api/assets/{symbol}/ai-insight?market=BR
**Get AI-powered recommendation for asset**

Response:
```json
{
  "symbol": "PETR4",
  "recommendation": "BUY",
  "confidence": 0.78,
  "reasoning": "RSI < 40 indicating oversold condition. MACD histogram positive with bullish crossover. Recent news on commodity prices mixed but technical setup is favorable.",
  "price_target": null,
  "model_used": "gpt-4o-mini",
  "generated_at": "2026-04-11T14:32:00Z"
}
```

#### GET /api/ai/opportunities?market=BR&num_picks=10
**Find top opportunities in market**

Response:
```json
{
  "market": "BR",
  "generated_at": "2026-04-11T06:00:00Z",
  "cache_expires_at": "2026-04-12T06:00:00Z",
  "opportunities": [
    {
      "symbol": "VALE3",
      "score": 87,
      "rationale": "Volume spike (3.2x avg), RSI < 30, MACD divergence. Commodity prices recovering.",
      "technicals": {
        "volume_ratio": 3.2,
        "rsi": 28,
        "price_change_pct": -4.8
      }
    },
    {
      "symbol": "PETR4",
      "score": 76,
      "rationale": "RSI oversold, golden cross forming. Oil prices stabilizing.",
      "technicals": {
        "volume_ratio": 1.8,
        "rsi": 35,
        "price_change_pct": -3.1
      }
    }
    // ... 8 more
  ]
}
```

---

### 3.3 Trade Endpoint (Extended)

#### POST /api/portfolios/{id}/trades?request_ai_validation=true
**Execute trade with optional AI review**

Request:
```json
{
  "asset_id": "uuid",
  "action": "BUY",
  "quantity": 20,
  "rationale": "User requested"
}
```

Response (with validation):
```json
{
  "trade": {
    "id": "uuid",
    "action": "BUY",
    "quantity": 20,
    "price": "29.50",
    "executed_at": "2026-04-11T14:35:00Z"
  },
  "ai_validation": {
    "approved": true,
    "suggested_quantity": 15,
    "reasoning": "Your portfolio is 45% in stocks. Reducing to 15 shares keeps position diversified.",
    "model_used": "gpt-4o-mini"
  },
  "portfolio_summary": { ... }
}
```

---

### 3.4 Backtesting Endpoints

#### POST /api/backtests
**Create new backtest scenario**

Request:
```json
{
  "name": "PETR4 Buy on Oversold",
  "description": "Buy PETR4 when RSI < 30, sell when RSI > 70",
  "asset_id": "uuid",
  "strategy": {
    "entry_condition": "rsi_14 < 30",
    "exit_condition": "rsi_14 > 70",
    "position_size_pct": 25
  },
  "date_from": "2025-10-11",
  "date_to": "2026-04-11"
}
```

Response:
```json
{
  "id": "uuid",
  "status": "queued",
  "created_at": "2026-04-11T14:40:00Z"
}
```

#### GET /api/backtests/{id}/status
**Check backtest progress**

Response:
```json
{
  "id": "uuid",
  "status": "running",
  "progress_pct": 45,
  "estimated_completion": "2026-04-11T14:55:00Z"
}
```

#### GET /api/backtests/{id}/results
**Retrieve backtest results**

Response:
```json
{
  "id": "uuid",
  "strategy": { ... },
  "date_range": { "from": "2025-10-11", "to": "2026-04-11" },
  "results": {
    "total_trades": 12,
    "winning_trades": 8,
    "losing_trades": 4,
    "win_rate_pct": 66.7,
    "total_pnl_amount": "450.50",
    "total_return_pct": 8.5,
    "max_drawdown_pct": -3.2,
    "avg_trade_duration_days": 21
  },
  "trade_log": [
    {
      "date": "2025-10-15",
      "symbol": "PETR4",
      "action": "BUY",
      "quantity": 20,
      "price": "28.50"
    },
    {
      "date": "2025-11-05",
      "symbol": "PETR4",
      "action": "SELL",
      "quantity": 20,
      "price": "31.20",
      "pnl": "54.00"
    }
    // ... more trades
  ]
}
```

---

## 4. Business Rules

### 4.1 OHLCV Backfill

**Provider Chain**:
1. Try Yahoo Finance
2. On failure, try Alpha Vantage
3. On failure, log error and mark asset as backfill-failed
4. Resume on next run

**Backfill Process**:
1. Fetch 5+ years of daily data per asset
2. Bulk insert into `ohlcv` table, ignore duplicate dates
3. Log success with date range covered
4. Mark asset as backfilled

### 4.2 Indicator Calculation

**Daily Calculation** (after market close):
1. For all assets with open positions or active alerts
2. Calculate all indicators using latest OHLCV
3. Store in database, replace previous day's indicators
4. Publish `indicators_calculated` event

**On-Demand Calculation** (when user views asset detail):
1. If indicators < 24 hours old, return cached
2. Otherwise, calculate immediately and cache
3. Require minimum 50 OHLCV rows; otherwise return empty

### 4.3 AI Features & Budget

**Initialization**:
- Users must add API key in Settings > AI before any AI feature works
- Default monthly budget: $10 USD
- Default alert threshold: 10% (warn at 90% consumed)

**Enforcement**:
- Before each AI call, check: `consumed_this_month >= monthly_budget`
- If true, raise `BudgetExceeded` exception
- View layer returns 402 (Payment Required) + error message
- User must increase budget or wait for next month

**Warnings**:
- When consumed >= (100% - alert_threshold_pct), show warning banner
- Example: "You've used 90% of your monthly AI budget ($9.00 / $10.00)"
- AI features still work, but warn each time

**Model Selection** (App-Driven):
- **Quick tasks** (asset insight, trade validation, news summary): Use fast model
  - OpenAI: GPT-4o-mini
  - Anthropic: Claude 3 Haiku
- **Complex tasks** (asset filtering): Use premium model
  - OpenAI: GPT-4 Turbo
  - Anthropic: Claude 3.5 Sonnet

**Cost Tracking**:
- Log every AI call to `AIUsage` table
- Include: prompt_tokens, completion_tokens, cost, feature, timestamp, month
- Monthly aggregation for dashboard report

### 4.4 Asset Filtering

**Two-Stage Process**:

**Stage 1 (Technical, No AI)**:
1. For each asset in market:
   - Volume > 2x 20-day average
   - Price moved ±5% yesterday
   - RSI crossing thresholds (e.g., crossing 30 or 70)
   - MACD divergences or histogram crossing
2. Return ~50 candidates

**Stage 2 (AI, Expensive)**:
1. Fetch recent news (last 5 headlines) for candidates
2. Call premium model: "Rank these {n} stocks by opportunity (0-100). Consider technicals, volume, and news."
3. Return top N with scores and rationales
4. Cache results for 24 hours (don't re-run unless forced)

**Optional Daily Task**:
- `scan_opportunities_daily` runs at market open
- Populates `/api/ai/opportunities` endpoint
- Can be disabled/enabled per user in Settings

### 4.5 News Integration

**Scraping Sources**:
- Yahoo Finance news (for each asset)
- Seeking Alpha headlines (if accessible)
- MarketWatch market news (general)
- Keep list modular; add/remove sources as needed

**Freshness**:
- Fetch on-demand when user views asset detail
- Cache for 4 hours
- Refresh daily as background task for tracked assets

**AI Summarization**:
- If news available, include in asset insight
- If news unavailable, show technicals only (no error)

### 4.6 Backtesting

**Engine Behavior**:
1. Load OHLCV for requested date range (default: 6 months)
2. For each day:
   - Update current price
   - Evaluate strategy entry/exit conditions
   - Execute simulated trades (don't touch real portfolio)
   - Track P&L
3. Return results: win rate, total P&L, max drawdown, trade log

**Limitations** (MLP scope):
- Single-asset, single-strategy only
- Entry/exit conditions are simple boolean expressions (RSI < 30, etc.)
- No portfolio-level simulation (trades don't affect cash)
- Results are read-only; can't save to portfolio

**Future (Post-MLP)**:
- Multi-asset strategies
- Complex conditions (e.g., RSI < 30 AND MACD > 0)
- Portfolio simulation (track cash impact)
- Save strategies + auto-trade execution

---

## 5. Frontend Specification

### 5.1 New Routes

| Route | Purpose |
|-------|---------|
| `/settings/ai` | AI configuration (key, budget, alert threshold) |
| `/assets/:symbol/analysis` | Extended asset detail with technicals + AI insight |
| `/ai/opportunities` | Daily AI picks by market |
| `/backtesting` | Backtest scenario builder + results |

### 5.2 Settings > AI Section

**Components**:
1. **AI Usage Report**:
   - Progress bar showing monthly consumption
   - Color: Green (0-50%) → Yellow/Orange (50-alert%) → Red (>alert%)
   - Tooltip on hover: `"AI: $X.XX / $Y.ZZ (P%)"`

2. **Configuration**:
   - Provider selector (OpenAI, Anthropic)
   - API key input (hidden, masked)
   - Monthly budget input ($)
   - Alert threshold input (%)
   - "Test Connection" button

3. **Usage Breakdown**:
   - Today: X calls, ~$Y.ZZ
   - This month: X calls, ~$Y.ZZ
   - Chart: Daily cost trend (last 30 days)

### 5.3 Asset Detail Page (Extended)

**New Tab: Analysis**:
1. **Technical Indicators Card**:
   - Candlestick chart (ApexCharts, 90-day default)
   - Indicator toggles: RSI, MACD, MAs, Bollinger Bands
   - Display current values and signals

2. **AI Insight Card** (if AI enabled):
   - Recommendation (BUY/SELL/HOLD)
   - Confidence score
   - Reasoning paragraph
   - Recent news snippets (if available)
   - "Refresh Insight" button

3. **Actions**:
   - [New Trade] button
   - [Create Alert] button
   - [Run Backtest] button

### 5.4 AI Opportunities Page

**Dashboard View**:
- Market selector (BR, US, UK, EU)
- Table of top 10 opportunities:
  - Symbol, Company Name
  - Opportunity Score (0-100)
  - Rationale (why ranked high)
  - Technicals (Volume ratio, RSI, Price change %)
  - [View Details], [Trade] buttons
- "Cache Expires: {time}" note
- [Refresh Now] button (if user has permission)

### 5.5 Header: AI Consumption Progress Bar

**Location**: Top-right, next to username / Logout

**Visual**:
- Compact progress bar: `[████░░░░]`
- Width: ~100px, Height: ~4px
- Label: "AI"
- Only visible if AI enabled

**Color Progression**:
- Green: 0–50% of budget
- Yellow: 50–(100% - alert_threshold%)
- Orange: (100% - alert_threshold%)–99%
- Red: >= 100% (budget exceeded)

**Hover Tooltip**:
- Show: `"AI: $X.XX / $Y.ZZ"`
- If over budget: `"AI: Budget exceeded. Disable AI or increase limit."`

### 5.6 Trade Form (Extended)

**New Section: AI Validation** (optional):
- Checkbox: "Get AI recommendation before confirming"
- If enabled, after user fills quantity:
  - Show AI validation: Approval + suggested quantity
  - User can accept suggestion or proceed with original quantity
  - If rejected by AI, show error message with reasoning

---

## 6. Background Jobs (Celery)

### 6.1 New Tasks

#### fetch_historical_ohlcv
**Backfill historical OHLCV for all assets**
- Trigger: Manual or scheduled (once per week)
- Provider chain: Yahoo Finance → Alpha Vantage
- Log successes and failures

#### calculate_indicators_daily
**Calculate daily indicators after market close**
- Trigger: Scheduled, after market close (e.g., 5 PM UTC)
- Assets: Those with open positions or active alerts
- Write to `TechnicalIndicators` table
- Publish `indicators_calculated` event

#### calculate_indicators_on_demand
**Immediate calculation when user views asset**
- Trigger: HTTP request from asset detail page
- Cache result for 24 hours
- Skip if insufficient OHLCV data

#### fetch_asset_news
**Scrape recent news for tracked assets**
- Trigger: Scheduled daily (morning, before market open)
- Assets: Those in user portfolios + watchlists
- Store headlines + snippets (keep most recent 5)
- Publish `news_fetched` event

#### scan_opportunities_daily
**Find high-potential assets via AI**
- Trigger: Optional, user-enabled, at market open
- Stage 1: Technical filter → ~50 candidates
- Stage 2: AI filtering → top 10
- Cache for 24 hours
- Publish `opportunities_found` event

#### calculate_backtest_async
**Long-running backtest simulation**
- Trigger: HTTP request from backtest form
- Run in background (Celery), update progress
- Return results when complete
- Store in `BacktestResult` table

---

## 7. Security and Reliability

### 7.1 API Key Management (BYOK)

**Storage**:
- Encrypt keys with Fernet (symmetric encryption)
- Never store plaintext
- Never log key value

**Usage**:
- Decrypt only when making API call
- Clear from memory immediately after use
- Include in error logs only as hashed reference

**Audit Trail**:
- Log when key added/updated/deleted (timestamp, user, provider)
- Log each AI API call (tokens, cost, feature, timestamp)
- Never log the key itself

### 7.2 Budget Enforcement

**Hard Stop**:
- Service layer checks budget before API call
- If exceeded, raise `BudgetExceeded` exception
- View layer returns 402 (Payment Required)
- User must increase budget or wait for next month

**Tracking**:
- Atomic: Insert `AIUsage` row AFTER successful API call
- If insertion fails, consider call as failed (don't charge user twice)
- Monthly aggregation: Reset on first day of month

### 7.3 Graceful Degradation

**If AI unavailable**:
- Return HTTP 503 or 429 (service unavailable / rate limited)
- Frontend disables AI buttons, shows message
- User can still use MVP features (trade, alerts, etc.)

**If news fetch fails**:
- Don't show news; show technicals only
- Log error, don't error out

**If backtesting fails**:
- Return error message with reason
- Let user retry or contact support

### 7.4 Rate Limiting

**AI calls**:
- No hard rate limit (respect user's API quota)
- Recommend max 10 calls/day for $10/month budget
- Show warning if approaching quota

**News scraping**:
- Respect robots.txt, user-agent headers
- Cache results (don't re-scrape same asset daily)
- Add delays between requests (1-2 sec per domain)

**Backtesting**:
- Only one backtest per user at a time (prevent CPU overload)
- Queue additional requests

---

## 8. Testing Requirements

### 8.1 Unit Tests

- Indicator calculations vs. pandas-ta reference
- BYOK key encryption/decryption
- Budget calculation (consumed vs. limit)
- Hard stop logic (prevent API call if over budget)
- Model selection per task
- Cost calculation per API call

### 8.2 Integration Tests

- OHLCV backfill with provider chain (mock providers)
- Daily indicator calculation end-to-end
- Asset filtering (technical + AI stages)
- Asset insight generation
- Trade validation with AI response
- Budget enforcement across multiple calls
- Backtest simulation and results calculation
- News fetching and caching

### 8.3 Manual Testing Checklist

- [ ] Backfill one asset, verify OHLCV data quality
- [ ] Add OpenAI API key in Settings
- [ ] View asset with technicals; verify indicators display
- [ ] Request asset insight; verify AI response format
- [ ] Set monthly budget to $0.50, verify hard stop kicks in
- [ ] Set alert threshold to 80%, verify warning at 80% consumed
- [ ] Run asset filter; verify top 10 opportunities
- [ ] Create backtest scenario (6 months), verify results
- [ ] Check header progress bar: Green → Yellow → Red as budget consumed
- [ ] Disable AI, verify AI buttons greyed out

---

## 9. Delivery Checklist

### Week 1: OHLCV Foundation
- [ ] `OHLCV` model + migration
- [ ] Yahoo Finance + Alpha Vantage fetchers
- [ ] Backfill Celery task with fallback
- [ ] Daily OHLCV collection in `fetch_market_prices`
- [ ] Provider fallback tests

### Week 2: Technical Indicators
- [ ] `TechnicalIndicators` model + migration
- [ ] `IndicatorCalculator` service (pandas-ta)
- [ ] Daily indicator Celery task
- [ ] On-demand endpoint + caching
- [ ] Indicator calculation tests

### Week 3: AI Infrastructure
- [ ] `AIAuth` + `AIUsage` models + migrations
- [ ] Key encryption (Fernet)
- [ ] Settings endpoints (add/remove/update)
- [ ] `AIService` abstraction (OpenAI + Anthropic)
- [ ] Usage tracking + cost calculation
- [ ] Hard stop + warning logic
- [ ] Header UI for progress bar

### Week 4: Asset Filtering + News
- [ ] News scraper (BeautifulSoup + sources)
- [ ] Stage 1 technical filter
- [ ] Stage 2 AI filtering
- [ ] `/api/ai/opportunities` endpoint
- [ ] Optional daily scan task
- [ ] News caching

### Week 5: AI Insights + Trade Validation
- [ ] Asset analysis service (indicators + news)
- [ ] `/api/assets/{symbol}/ai-insight` endpoint
- [ ] Trade validation extension
- [ ] Frontend: AI insight card
- [ ] Model selection per task type
- [ ] Integration tests

### Week 6: Backtesting + Polish
- [ ] `backtesting` app structure
- [ ] `BacktestEngine` core
- [ ] `/api/backtests` endpoints
- [ ] Backtest on 6-month range
- [ ] Error handling + graceful degradation
- [ ] Full integration tests
- [ ] Documentation

---

## 10. Known Decisions

✅ **BYOK Primary**: No live OAuth service. Code structure ready for future plug-and-play.
✅ **Hard Stop Enforcement**: Budget exceeded = disable AI features, not just warn.
✅ **App-Driven Models**: Quick vs. complex tasks use different models; users don't choose per task.
✅ **News via Scraping**: Start here; RSS feeds in post-MLP.
✅ **Backtesting Isolated**: Separate app, 6-month simulations, single-strategy only (MLP scope).
✅ **Budget Default**: $10/month, alert at 10% remaining, monthly reset.
✅ **Header Progress Bar**: Always visible if AI enabled; color gradient + tooltip.

