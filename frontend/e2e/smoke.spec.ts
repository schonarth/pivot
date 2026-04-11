import { test, expect } from '@playwright/test'

test.describe('Smoke Tests - Core Flows', () => {
  test('Login page renders', async ({ page }) => {
    await page.goto('/login')
    await expect(page.locator('.auth-container')).toBeVisible()
    await expect(page.locator('h2')).toContainText('Login')
    await expect(page.locator('input[type="text"]')).toBeVisible()
    await expect(page.locator('input[type="password"]')).toBeVisible()
    await expect(page.locator('button')).toBeVisible()
  })

  test('Register page renders', async ({ page }) => {
    await page.goto('/register')
    await expect(page.locator('.auth-container')).toBeVisible()
    await expect(page.locator('h2')).toContainText('Register')
    await expect(page.locator('input[type="email"]')).toBeVisible()
    await expect(page.locator('input[type="text"]')).toBeVisible()
    await expect(page.locator('input[type="password"]')).toBeVisible()
    await expect(page.locator('button')).toBeVisible()
  })

  test('App renders without crashing', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('body')).toBeVisible()
  })
})

test.describe('Authentication Flow', () => {
  test('Registration creates account and logs in', async ({ page, request }) => {
    const testUsername = `user_${Date.now()}`
    const testEmail = `${testUsername}@test.com`
    const testPassword = 'TestPass123!'

    const response = await request.post('http://localhost:8000/api/auth/register', {
      data: {
        username: testUsername,
        email: testEmail,
        password: testPassword,
      },
    })

    expect(response.status()).toBe(201)
    const data = await response.json()
    expect(data.user).toBeDefined()
    expect(data.access).toBeDefined()
    expect(data.refresh).toBeDefined()
  })

  test('Login with valid credentials succeeds', async ({ request }) => {
    const testUsername = `testuser_${Date.now()}`
    const testPassword = 'TestPass123!'

    const registerResponse = await request.post('http://localhost:8000/api/auth/register', {
      data: {
        username: testUsername,
        email: `${testUsername}@test.com`,
        password: testPassword,
      },
    })
    expect(registerResponse.status()).toBe(201)

    const loginResponse = await request.post('http://localhost:8000/api/auth/login', {
      data: {
        username: testUsername,
        password: testPassword,
      },
    })
    expect(loginResponse.status()).toBe(200)
    const data = await loginResponse.json()
    expect(data.access).toBeDefined()
  })

  test('Login with invalid credentials fails', async ({ request }) => {
    const response = await request.post('http://localhost:8000/api/auth/login', {
      data: {
        username: 'nonexistent',
        password: 'wrongpass',
      },
    })
    expect(response.status()).toBe(401)
  })
})

test.describe('Portfolio Management Flow', () => {
  test('Create and retrieve portfolio', async ({ request }) => {
    const testUsername = `portfolio_user_${Date.now()}`
    const testPassword = 'TestPass123!'

    const registerResponse = await request.post('http://localhost:8000/api/auth/register', {
      data: {
        username: testUsername,
        email: `${testUsername}@test.com`,
        password: testPassword,
      },
    })
    const registerData = await registerResponse.json()
    const accessToken = registerData.access

    const portfolioResponse = await request.post('http://localhost:8000/api/portfolios/', {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
      data: {
        name: 'Test Portfolio',
        market: 'US',
        initial_capital: '10000.00',
      },
    })
    expect(portfolioResponse.status()).toBe(201)
    const portfolioData = await portfolioResponse.json()
    expect(portfolioData.name).toBe('Test Portfolio')
    expect(portfolioData.market).toBe('US')
    expect(portfolioData.current_cash).toBe('10000.00')

    const getResponse = await request.get(`http://localhost:8000/api/portfolios/${portfolioData.id}/`, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    })
    expect(getResponse.status()).toBe(200)
    const getData = await getResponse.json()
    expect(getData.id).toBe(portfolioData.id)
  })

  test('Deposit to portfolio', async ({ request }) => {
    const testUsername = `deposit_user_${Date.now()}`
    const testPassword = 'TestPass123!'

    const registerResponse = await request.post('http://localhost:8000/api/auth/register', {
      data: {
        username: testUsername,
        email: `${testUsername}@test.com`,
        password: testPassword,
      },
    })
    const registerData = await registerResponse.json()
    const accessToken = registerData.access

    const portfolioResponse = await request.post('http://localhost:8000/api/portfolios/', {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
      data: {
        name: 'Test Portfolio',
        market: 'US',
        initial_capital: '10000.00',
      },
    })
    const portfolioData = await portfolioResponse.json()
    const portfolioId = portfolioData.id

    const depositResponse = await request.post(
      `http://localhost:8000/api/portfolios/${portfolioId}/deposit/`,
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
        data: {
          amount: '5000.00',
        },
      }
    )
    expect(depositResponse.status()).toBe(200)
    const depositData = await depositResponse.json()
    expect(depositData.cash).toBe('15000.00')
  })

  test('Withdraw from portfolio', async ({ request }) => {
    const testUsername = `withdraw_user_${Date.now()}`
    const testPassword = 'TestPass123!'

    const registerResponse = await request.post('http://localhost:8000/api/auth/register', {
      data: {
        username: testUsername,
        email: `${testUsername}@test.com`,
        password: testPassword,
      },
    })
    const registerData = await registerResponse.json()
    const accessToken = registerData.access

    const portfolioResponse = await request.post('http://localhost:8000/api/portfolios/', {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
      data: {
        name: 'Test Portfolio',
        market: 'US',
        initial_capital: '10000.00',
      },
    })
    const portfolioData = await portfolioResponse.json()
    const portfolioId = portfolioData.id

    const withdrawResponse = await request.post(
      `http://localhost:8000/api/portfolios/${portfolioId}/withdraw/`,
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
        data: {
          amount: '2000.00',
        },
      }
    )
    expect(withdrawResponse.status()).toBe(200)
    const withdrawData = await withdrawResponse.json()
    expect(withdrawData.cash).toBe('8000.00')
  })
})

test.describe('API Endpoints - Basic Health Checks', () => {
  test('API root endpoint responds', async ({ request }) => {
    const response = await request.get('http://localhost:8000/')
    expect(response.status()).toBe(200)
    const data = await response.json()
    expect(data.name).toBe('Paper Trader API')
  })

  test('Markets endpoint requires authentication', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/markets/status/')
    expect(response.status()).toBe(401)
  })

  test('Assets endpoint requires authentication', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/assets/')
    expect(response.status()).toBe(401)
  })

  test('Portfolios endpoint requires authentication', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/portfolios/')
    expect(response.status()).toBe(401)
  })
})
