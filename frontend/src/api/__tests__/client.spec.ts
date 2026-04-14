import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from '@/api'
import {
  clearSession,
  resetSessionForTests,
  setAccessToken,
  setAuthFailureHandler,
  setRefreshHandler,
} from '@/auth/session'

function encodeBase64Url(value: string) {
  return btoa(value).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '')
}

function createToken(expirationMs: number) {
  const header = encodeBase64Url(JSON.stringify({ alg: 'none', typ: 'JWT' }))
  const payload = encodeBase64Url(JSON.stringify({ exp: Math.floor(expirationMs / 1000) }))
  return `${header}.${payload}.signature`
}

describe('api client auth flow', () => {
  const originalAdapter = api.defaults.adapter

  beforeEach(() => {
    resetSessionForTests()
  })

  afterEach(() => {
    api.defaults.adapter = originalAdapter
    clearSession()
    resetSessionForTests()
    vi.restoreAllMocks()
  })

  it('refreshes once and retries the original request', async () => {
    const firstToken = createToken(Date.now() + 120_000)
    const refreshedToken = createToken(Date.now() + 300_000)
    const requests: Array<{ headers: Record<string, unknown>; retry?: boolean }> = []

    setAccessToken(firstToken)
    setRefreshHandler(async () => refreshedToken)
    setAuthFailureHandler(vi.fn())

    api.defaults.adapter = async (config) => {
      requests.push({
        headers: { ...(config.headers as Record<string, unknown>) },
        retry: (config as { _retry?: boolean })._retry,
      })

      if (requests.length === 1) {
        return Promise.reject({
          config,
          response: { status: 401, config, data: {} },
        })
      }

      return {
        data: { ok: true },
        status: 200,
        statusText: 'OK',
        headers: {},
        config,
      }
    }

    const response = await api.get('/protected')

    expect(response.data).toEqual({ ok: true })
    expect(requests).toHaveLength(2)
    expect(String(requests[0].headers.Authorization || requests[0].headers.authorization)).toBe(`Bearer ${firstToken}`)
    expect(String(requests[1].headers.Authorization || requests[1].headers.authorization)).toBe(`Bearer ${refreshedToken}`)
  })

  it('redirects through the auth failure handler when refresh fails', async () => {
    const authFailureHandler = vi.fn()

    window.history.pushState({}, '', '/portfolio-detail?tab=positions')
    setAccessToken(createToken(Date.now() + 120_000))
    setRefreshHandler(async () => {
      throw new Error('expired')
    })
    setAuthFailureHandler(authFailureHandler)

    api.defaults.adapter = async (config) => {
      return Promise.reject({
        config,
        response: { status: 401, config, data: {} },
      })
    }

    await expect(api.get('/protected')).rejects.toBeTruthy()
    expect(authFailureHandler).toHaveBeenCalledWith('/portfolio-detail?tab=positions')
  })

  it('does not refresh or redirect for permission errors', async () => {
    const refreshHandler = vi.fn()
    const authFailureHandler = vi.fn()

    setRefreshHandler(refreshHandler)
    setAuthFailureHandler(authFailureHandler)

    api.defaults.adapter = async (config) => {
      return Promise.reject({
        config,
        response: { status: 403, config, data: {} },
      })
    }

    await expect(api.get('/protected')).rejects.toBeTruthy()
    expect(refreshHandler).not.toHaveBeenCalled()
    expect(authFailureHandler).not.toHaveBeenCalled()
  })
})
