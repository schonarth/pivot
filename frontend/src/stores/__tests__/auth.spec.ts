import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useAuthStore } from '../auth'
import * as authApi from '@/api/auth'
import {
  clearSession,
  getAccessToken,
  resetSessionForTests,
  setAccessToken,
  setRefreshHandler,
} from '@/auth/session'

vi.mock('@/api/auth', () => ({
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
  getMe: vi.fn(),
}))

function encodeBase64Url(value: string) {
  return btoa(value).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '')
}

function createToken(expirationMs: number) {
  const header = encodeBase64Url(JSON.stringify({ alg: 'none', typ: 'JWT' }))
  const payload = encodeBase64Url(JSON.stringify({ exp: Math.floor(expirationMs / 1000) }))
  return `${header}.${payload}.signature`
}

describe('auth store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    resetSessionForTests()
    clearSession()
    vi.clearAllMocks()
  })

  it('stores tokens and user data on login', async () => {
    vi.mocked(authApi.login).mockResolvedValue({
      user: {
        id: '1',
        api_uuid: '00000000-0000-0000-0000-000000000001',
        username: 'alice',
        email: 'alice@example.com',
        first_name: '',
        last_name: '',
      },
      access: createToken(Date.now() + 120_000),
    })

    const store = useAuthStore()
    await store.login('alice', 'password123')

    expect(store.isAuthenticated).toBe(true)
    expect(store.user?.username).toBe('alice')
    expect(getAccessToken()).not.toBeNull()
    expect(authApi.login).toHaveBeenCalledWith('alice', 'password123')
  })

  it('rehydrates a session with a silent refresh when requested', async () => {
    const refreshedToken = createToken(Date.now() + 300_000)
    setRefreshHandler(async () => refreshedToken)

    const store = useAuthStore()
    await store.initialize({ forceRefresh: true })

    expect(store.initialized).toBe(true)
    expect(store.isAuthenticated).toBe(true)
    expect(getAccessToken()).toBe(refreshedToken)
  })

  it('logs out through the backend and clears the local session', async () => {
    vi.mocked(authApi.logout).mockResolvedValue(undefined)
    setAccessToken(createToken(Date.now() + 120_000))

    const store = useAuthStore()
    store.$patch({
      user: {
        id: '1',
        api_uuid: '00000000-0000-0000-0000-000000000001',
        username: 'alice',
        email: 'alice@example.com',
        first_name: '',
        last_name: '',
      },
    })

    await store.logout()

    expect(authApi.logout).toHaveBeenCalledTimes(1)
    expect(store.isAuthenticated).toBe(false)
    expect(store.user).toBeNull()
    expect(getAccessToken()).toBeNull()
  })
})
