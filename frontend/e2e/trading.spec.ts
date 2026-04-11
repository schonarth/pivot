import { test, expect } from '@playwright/test'

test.describe('Trading Flow', () => {
  test('List assets after authentication', async ({ request }) => {
    const testUsername = `assets_user_${Date.now()}`
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

    const response = await request.get('http://localhost:8000/api/assets/', {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    })
    expect(response.status()).toBe(200)
    const data = await response.json()
    expect(Array.isArray(data)).toBe(true)
  })

  test('Get market status', async ({ request }) => {
    const testUsername = `market_user_${Date.now()}`
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

    const response = await request.get('http://localhost:8000/api/markets/status', {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    })
    expect(response.status()).toBe(200)
    const data = await response.json()
    expect(data).toBeDefined()
  })

  test('Get portfolio summary', async ({ request }) => {
    const testUsername = `summary_user_${Date.now()}`
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
        name: 'Summary Test Portfolio',
        market: 'US',
        initial_capital: '50000.00',
      },
    })
    const portfolioData = await portfolioResponse.json()

    const summaryResponse = await request.get(
      `http://localhost:8000/api/portfolios/${portfolioData.id}/summary/`,
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      }
    )
    expect(summaryResponse.status()).toBe(200)
    const summaryData = await summaryResponse.json()
    expect(summaryData).toBeDefined()
  })

  test('List positions in portfolio', async ({ request }) => {
    const testUsername = `positions_user_${Date.now()}`
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
        name: 'Positions Test Portfolio',
        market: 'US',
        initial_capital: '50000.00',
      },
    })
    const portfolioData = await portfolioResponse.json()

    const positionsResponse = await request.get(
      `http://localhost:8000/api/portfolios/${portfolioData.id}/positions/`,
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      }
    )
    expect(positionsResponse.status()).toBe(200)
    const positionsResponseData = await positionsResponse.json()
    const positionsData = positionsResponseData.results || positionsResponseData
    expect(Array.isArray(positionsData)).toBe(true)
  })

  test('List trades in portfolio', async ({ request }) => {
    const testUsername = `trades_user_${Date.now()}`
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
        name: 'Trades Test Portfolio',
        market: 'US',
        initial_capital: '50000.00',
      },
    })
    const portfolioData = await portfolioResponse.json()

    const tradesResponse = await request.get(
      `http://localhost:8000/api/portfolios/${portfolioData.id}/trades/`,
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      }
    )
    expect(tradesResponse.status()).toBe(200)
    const tradesResponseData = await tradesResponse.json()
    const tradesData = tradesResponseData.results || tradesResponseData
    expect(Array.isArray(tradesData)).toBe(true)
  })
})

test.describe('Alerts Flow', () => {
  test('List alerts in portfolio', async ({ request }) => {
    const testUsername = `alerts_user_${Date.now()}`
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
        name: 'Alerts Test Portfolio',
        market: 'US',
        initial_capital: '50000.00',
      },
    })
    const portfolioData = await portfolioResponse.json()

    const alertsResponse = await request.get(
      `http://localhost:8000/api/portfolios/${portfolioData.id}/alerts/`,
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      }
    )
    expect(alertsResponse.status()).toBe(200)
    const alertsResponseData = await alertsResponse.json()
    const alertsData = alertsResponseData.results || alertsResponseData
    expect(Array.isArray(alertsData)).toBe(true)
  })

  test('List alert triggers', async ({ request }) => {
    const testUsername = `triggers_user_${Date.now()}`
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

    const triggersResponse = await request.get('http://localhost:8000/api/alert-triggers/', {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    })
    expect(triggersResponse.status()).toBe(200)
    const triggersResponseData = await triggersResponse.json()
    const triggersData = triggersResponseData.results || triggersResponseData
    expect(Array.isArray(triggersData)).toBe(true)
  })
})
