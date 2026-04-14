import { ref } from 'vue'

const accessToken = ref<string | null>(null)
let refreshTimer: ReturnType<typeof window.setTimeout> | null = null
let refreshHandler: (() => Promise<string>) | null = null
let authFailureHandler: ((redirectTo: string) => void) | null = null
let refreshPromise: Promise<string | null> | null = null

function decodeJwtExpiry(token: string): number | null {
  const parts = token.split('.')
  if (parts.length < 2) return null

  try {
    const payload = JSON.parse(window.atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')))
    return typeof payload.exp === 'number' ? payload.exp * 1000 : null
  } catch {
    return null
  }
}

function clearRefreshTimer() {
  if (refreshTimer) {
    window.clearTimeout(refreshTimer)
    refreshTimer = null
  }
}

function scheduleRefresh(token: string) {
  clearRefreshTimer()

  const expiresAt = decodeJwtExpiry(token)
  if (!expiresAt) return

  const leadTime = 60_000
  const delay = Math.max(expiresAt - Date.now() - leadTime, 0)
  refreshTimer = window.setTimeout(() => {
    void refreshAccessToken()
  }, delay)
}

function currentRedirectPath() {
  return `${window.location.pathname}${window.location.search}`
}

export function setRefreshHandler(handler: () => Promise<string>) {
  refreshHandler = handler
}

export function setAuthFailureHandler(handler: (redirectTo: string) => void) {
  authFailureHandler = handler
}

export function getAccessToken() {
  return accessToken.value
}

export function hasAccessToken() {
  return !!accessToken.value
}

export function setAccessToken(token: string) {
  accessToken.value = token
  scheduleRefresh(token)
}

export function clearSession() {
  accessToken.value = null
  clearRefreshTimer()
  refreshPromise = null
}

export function handleAuthFailure(redirectTo = currentRedirectPath()) {
  clearSession()
  authFailureHandler?.(redirectTo)
}

export async function refreshAccessToken(): Promise<string | null> {
  if (!refreshHandler) return null
  if (refreshPromise) return refreshPromise

  refreshPromise = refreshHandler()
    .then((token) => {
      setAccessToken(token)
      return token
    })
    .catch(() => {
      handleAuthFailure()
      return null
    })
    .finally(() => {
      refreshPromise = null
    })

  return refreshPromise
}

export function resetSessionForTests() {
  clearSession()
  refreshHandler = null
  authFailureHandler = null
}
