# <img src="./frontend/public/pivot-logo.png" alt="Pivot Logo" style="float: left; width: 20px; margin: 0 20px 20px 0;" /> Pivot

**A paper trading simulator** for learning investment strategies, testing alerts, and experimenting with portfolio management across global markets without risking real capital.

*With MCP server* — Use your AI agents to automate trading, analyze portfolios, and manage alerts!

---

## What You Can Do

- **Paper trade** across 4 global markets: Brazil, US, UK, and Europe
- **Set price alerts** that notify you or automatically execute trades
- **Simulate market prices** to test your strategies when markets are closed
- **Track portfolio performance** with real-time updates
- **Manage multiple portfolios** for different investment goals

Perfect for developing trading strategies, testing alert logic, and learning portfolio management in a risk-free environment.

---

## Getting Started

### Requirements

You only need **Docker**. That's it.

**Don't have Docker?**
- [Download Docker Desktop](https://www.docker.com/products/docker-desktop) (includes Docker Compose)
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

**Simulate specific market:**
```bash
./simulate_market.sh BR
```

**Simulate specific assets:**
```bash
./simulate_market.sh AAPL MSFT
```

The simulator updates prices in real-time—watch your portfolio react on the dashboard.

---

## AI Agents (MCP Server)

Connect AI agents to automate trading, analyze portfolios, and execute strategies.

**To set up agent access:** Go to Settings, get your UUID, and generate a one-time password (OTP). With these, your agent will be able to manage trades, alerts, and portfolios.

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
