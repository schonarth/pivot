# Testing Guide

This document describes the test structure and how to run tests for the Paper Trader application.

## Test Coverage Overview

### Backend Tests

Unit tests are implemented for all major Django apps using `pytest` and `pytest-django`:

- **accounts** (`backend/accounts/test_views.py`) - 8 tests
  - User registration, login, authentication, logout
  
- **markets** (`backend/markets/test_views.py`) - 10 tests
  - Asset listing and filtering, price quotes, market status
  
- **portfolios** (`backend/portfolios/test_views.py`) - 13 tests
  - Portfolio CRUD, deposits/withdrawals, cash transactions, performance summary
  
- **trading** (`backend/trading/test_views.py`) - 8 tests
  - Buy/sell operations, position management, trade execution with validation
  
- **alerts** (`backend/alerts/test_views.py`, `backend/alerts/test_services.py`, `backend/alerts/test_tasks.py`) - 22 tests
  - Alert creation/update, pause/resume, trigger evaluation, async task execution
  
**Total Backend Tests: 61 tests**

### Frontend Tests

Frontend tests use Vitest + Vue Test Utils for unit tests and Playwright for E2E tests:

- **Unit Tests** (`frontend/src/**/__tests__/*.spec.ts`)
  - LoginView, RegisterView, App component smoke tests
  
- **E2E Tests** (`frontend/e2e/*.spec.ts`)
  - smoke.spec.ts: Auth flow, portfolio management, API health checks
  - trading.spec.ts: Asset listing, trading operations, alerts

**Total Frontend Tests: 20+ test cases**

## Running Tests

### Backend Tests

```bash
# Install dependencies (if not already done)
cd backend
pip install -e ".[dev]"

# Run all tests
pytest

# Run tests for a specific app
pytest accounts/
pytest markets/
pytest portfolios/
pytest trading/
pytest alerts/

# Run tests with coverage
pytest --cov

# Run tests in verbose mode
pytest -v

# Run a specific test class
pytest alerts/test_services.py::TestEvaluateAlertPriceAbove

# Run a specific test
pytest alerts/test_services.py::TestEvaluateAlertPriceAbove::test_fires_when_price_exceeds_threshold
```

### Frontend Unit Tests

```bash
# Install dependencies (if not already done)
cd frontend
npm install

# Run all unit tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with UI
npm run test:ui

# Run tests for a specific file
npm test LoginView.spec.ts
```

### Frontend E2E Tests

```bash
# Install dependencies (if not already done)
cd frontend
npm install

# Run all E2E tests
npm run test:e2e

# Run E2E tests in UI mode (interactive)
npm run test:e2e:ui

# Run tests for a specific file
npm run test:e2e -- smoke.spec.ts

# Run a specific test
npm run test:e2e -- --grep "Registration creates account"
```

## Test Architecture

### Backend Test Fixtures

The `conftest.py` file provides reusable factories for common models:

- `UserFactory` - Create test users
- `AssetFactory` - Create test assets
- `AssetQuoteFactory` - Create price quotes
- `PortfolioFactory` - Create test portfolios
- `PositionFactory` - Create positions
- `TradeFactory` - Create trades
- `AlertFactory` - Create alerts
- `AlertTriggerFactory` - Create alert triggers

Example usage in tests:

```python
def test_something(portfolio, asset):
    # portfolio and asset are automatically created fixtures
    pass

def test_with_factory(db):
    from conftest import TradeFactory
    trade = TradeFactory(quantity=50)
```

### Frontend Test Setup

- **Unit Tests**: Vitest with jsdom environment
- **E2E Tests**: Playwright with Chrome/Chromium
- **API Mocking**: Real API calls to test backend (cleanup is automatic)

## Continuous Integration

Tests are designed to run in CI/CD pipelines:

- Backend tests use `pytest` with Django test database
- Frontend tests use Vitest and Playwright with headless Chrome
- All tests create and clean up their own test data automatically

## Test Data Cleanup

- **Backend**: Django test database is automatically created and destroyed per test session
- **Frontend E2E**: Test portfolios are created with unique timestamps; manual cleanup can be done via DELETE /api/portfolios/{id}/ if needed
- **Fixtures**: Each test uses fresh fixture instances

## Common Test Patterns

### Testing Authenticated Endpoints (Backend)

```python
def test_something(authenticated_client, portfolio):
    response = authenticated_client.get(f'/api/portfolios/{portfolio.id}/')
    assert response.status_code == 200
```

### Testing with Factory Fixtures (Backend)

```python
def test_create_trade(authenticated_client, portfolio_with_cash, asset_with_quote):
    response = authenticated_client.post(
        f'/api/portfolios/{portfolio_with_cash.id}/trades/',
        {'asset_id': str(asset_with_quote.id), 'action': 'BUY', 'quantity': '10'},
        format='json'
    )
    assert response.status_code == 201
```

### Testing API Integration (Frontend E2E)

```typescript
test('Create portfolio succeeds', async ({ request }) => {
  const response = await request.post('http://localhost:8000/api/portfolios/', {
    headers: { Authorization: `Bearer ${token}` },
    data: { name: 'Test', market: 'US', initial_capital: '10000' }
  })
  expect(response.status()).toBe(201)
})
```

## Debugging Tests

### Backend

```bash
# Add print statements and run with -s flag
pytest -s alerts/test_services.py

# Run with detailed output
pytest -vv alerts/test_services.py

# Stop on first failure
pytest -x alerts/test_services.py

# Drop into pdb on failure
pytest --pdb alerts/test_services.py
```

### Frontend Unit Tests

```bash
npm test -- --reporter=verbose
npm test -- --reporter=html  # Generate HTML report
```

### Frontend E2E Tests

```bash
# Run with headed browser (see what's happening)
npm run test:e2e -- --headed

# Run in debug mode (step through)
npm run test:e2e -- --debug

# Generate trace artifacts
npm run test:e2e -- --trace on
```

## Test Coverage Goals

- **Backend**: All views/endpoints tested with happy path and error cases
- **Frontend**: All main components render without crashing
- **Integration**: Critical user flows (auth → trade → view results) work end-to-end

## Known Limitations

1. **Email**: Tests don't verify actual email sending
2. **Real Quotes**: E2E tests may use cached or missing price data (tests use existing assets)
3. **WebSocket**: Realtime consumer not directly tested (covered by integration tests)
4. **File Uploads**: Not tested (none currently in app)

## Future Improvements

- Add performance benchmarks
- Add visual regression tests
- Increase frontend unit test coverage beyond smoke tests
- Test WebSocket connections with mock server
- Add load testing for API endpoints
