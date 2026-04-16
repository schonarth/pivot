import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  clearSession,
  getAccessToken,
  refreshAccessToken,
  resetSessionForTests,
  setAccessToken,
  setAuthFailureHandler,
  setRefreshHandler,
} from '../session'

function encodeBase64Url(value: string) {
  return btoa(value).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '')
}

function createToken(expirationMs: number) {
  const header = encodeBase64Url(JSON.stringify({ alg: 'none', typ: 'JWT' }))
  const payload = encodeBase64Url(JSON.stringify({ exp: Math.floor(expirationMs / 1000) }))
  return `${header}.${payload}.signature`
}

describe('auth session', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-01-01T00:00:00Z'))
    resetSessionForTests()
  })

  afterEach(() => {
    clearSession()
    resetSessionForTests()
    vi.useRealTimers()
  })

  it('refreshes proactively before the access token expires', async () => {
    const nextToken = createToken(Date.now() + 5 * 60_000)
    const refreshHandler = vi.fn().mockResolvedValue(nextToken)
    setRefreshHandler(refreshHandler)
    setAuthFailureHandler(vi.fn())

    setAccessToken(createToken(Date.now() + 120_000))

    await vi.advanceTimersByTimeAsync(59_000)
    expect(refreshHandler).not.toHaveBeenCalled()

    await vi.advanceTimersByTimeAsync(1_000)
    expect(refreshHandler).toHaveBeenCalledTimes(1)
    expect(getAccessToken()).toBe(nextToken)
  })

  it('clears the session and signals auth failure when refresh cannot recover', async () => {
    const authFailureHandler = vi.fn()
    setAuthFailureHandler(authFailureHandler)
    setRefreshHandler(vi.fn().mockRejectedValue(new Error('expired')))

    window.history.pushState({}, '', '/portfolio-detail?tab=positions')
    setAccessToken(createToken(Date.now() + 120_000))

    await expect(refreshAccessToken()).resolves.toBeNull()
    expect(authFailureHandler).toHaveBeenCalledWith('/portfolio-detail?tab=positions')
    expect(getAccessToken()).toBeNull()
  })
})
