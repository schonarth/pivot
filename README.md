# ![Pivot logo](./frontend/public/pivot-logo.png) Pivot


**An AI-powered paper trading simulator** for developing and testing investment strategies across global markets without risking real capital. Build strategies, get AI-generated insights, backtest with real market data, and execute trades, all risk-free — or let your AI agent do it for you with MCP support!

---

## What You Can Do

- **Develop strategies** with technical indicators and backtesting engine
- **Get AI insights** — Technical analysis powered by your choice of AI providers
- **Backtest strategies** against historical OHLCV data
- **Paper trade** across 4 global markets: Brazil, US, UK, and Europe
- **Set smart alerts** that trigger trades automatically when conditions are met
- **Simulate market prices** to test strategies when markets are closed
- **Manage multiple portfolios** for different investment goals and risk profiles
- **Bring your AI agent** to trade with you with our simple to setup MCP server

Perfect for developing trading strategies, testing alert logic, learning portfolio management, and experimenting with automated trading — all without risking real capital.

---

## Getting Started

### Requirements

You only need **Docker**. That's it.

**Don't have Docker?**
- [Download Docker Desktop](https://www.docker.com/products/docker-desktop)
- Install and run it

### Start the Application

Once Docker is running:

**Linux/Mac:**
```bash
./start.sh
```

**Windows:**
```bash
start.bat
```

The application will be ready at `http://localhost:3000` in about 30 seconds.

### First Time Setup

1. Open `http://localhost:3000` in your browser
2. Register with an email and password
3. Create your first portfolio (choose a market)
4. Deposit starting capital
5. Start trading!

---

## Features

### Strategy Development
- **Build strategies** with technical indicators (moving averages, RSI, MACD, Bollinger Bands, and more)
- **Backtest** strategies against historical OHLCV data
- **Monitor execution** — Track autonomous trades triggered by your strategies
- **Test and iterate** — Refine rules before deploying to live trading

### AI-Powered Insights
- **Generate technical analysis** — Claude, GPT, and Gemini supported now for market insights
- **Budget tracking** — Monitor AI provider costs and set spending limits (API key required — sorry, no flat rate support 😅)

### Portfolios
- Create separate portfolios for different markets
- Track cash, invested value, and profit/loss
- View performance history and returns
- Deposit or withdraw funds anytime

### Trading
- Buy and sell stocks/ETFs with automatic fee calculation
- Track your positions and average costs
- View current prices and unrealized gains/losses

### Price Alerts
- Set alerts when prices go above or below your target
- Get notified when alerts trigger
- Automatically execute trades when conditions are met
- Choose fixed quantity or percentage-based trades

### Market Simulation
Test your strategies when markets are closed:

**Quick price update:**
```bash
./simulate_price.sh AAPL 150.00
```

**Run realistic market movement:**
```bash
./simulate_market.sh
```

**Simulate with directional trends:**
```bash
./simulate_market.sh --trends AAPL MSFT
```

**Simulate specific market:**
```bash
./simulate_market.sh BR
```

The simulator updates prices in real-time—watch your portfolio and strategies react on the dashboard.

> [!IMPORTANT]
> To enable alerts for simaulated market, you must turn on the **simulation toggle** on your portfolios.

> [!TIP]
> Use different portfolios to run simulations and for actual market tracking, to prevent distortions.

---

## AI-Powered Automation (MCP Server)

Use AI agents to automate trading, backtest strategies, generate insights, and manage your portfolio.

**Agent capabilities:**
- Manage trades, alerts, and portfolios
- Backtest trading strategies against historical data
- Generate technical analysis and trading insights
- Monitor strategy execution and autonomous trades
- Manage AI provider settings and cost budgets

**To set up agent access:**
1. Go to Settings
2. Get your User UUID
3. Generate a one-time password (OTP)
4. Your agent will have full access to manage trading, backtesting, and insights

---

## Supported Markets

| Market | Currency | Trading Fee | Exchange |
|--------|----------|-------------|----------|
| Brazil | BRL | 0.03% | BVMF |
| United States | USD | 0% | XNYS |
| United Kingdom | GBP | 0.1% | XLON |
| Europe | EUR | 0.1% | XPAR |

---

## Troubleshooting

**"Can't connect to http://localhost:3000"**
- Make sure Docker is running
- Run the start script again
- Wait 30 seconds for services to initialize
- If you're accessing from a different machine than you're running the Pivot server, replace `localhost` with the server's IP address.

**"Application won't load"**
- Check that port 3000 isn't in use by another application
- Restart Docker

**"Simulator not updating prices"**
- Make sure the application is running (`./start.sh` or `start.bat`)
- Try a fresh start: stop the application and run the start script again

**Need to stop the application?**
```bash
docker compose down
```

---

## License

MIT License. See LICENSE file for details.

---

**Built with ❤️ for learning and experimentation.**
