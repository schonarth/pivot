import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'
import type { User } from '@/types'
import * as authApi from '@/api/auth'
import { clearSession, getAccessToken, hasAccessToken, refreshAccessToken, setAccessToken } from '@/auth/session'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const initialized = ref(false)
  const isAuthenticated = computed(() => hasAccessToken())
  let initializing: Promise<void> | null = null

  watch(
    () => getAccessToken(),
    (token) => {
      if (!token) {
        user.value = null
      }
    },
  )

  async function login(username: string, password: string) {
    const data = await authApi.login(username, password)
    setAccessToken(data.access)
    user.value = data.user
    initialized.value = true
  }

  async function register(username: string, email: string, password: string) {
    const data = await authApi.register(username, email, password)
    setAccessToken(data.access)
    user.value = data.user
    initialized.value = true
  }

  async function fetchUser() {
    try {
      user.value = await authApi.getMe()
      initialized.value = true
    } catch {
      void logout()
    }
  }

  async function initialize(options: { forceRefresh?: boolean } = {}) {
    if (initializing) return initializing

    const { forceRefresh = false } = options
    if (initialized.value && (!forceRefresh || hasAccessToken())) return

    initializing = (async () => {
      if (hasAccessToken()) {
        initialized.value = true
        return
      }

      if (forceRefresh) {
        await refreshAccessToken()
      }
      initialized.value = true
    })().finally(() => {
      initializing = null
    })

    return initializing
  }

  async function logout() {
    await authApi.logout().catch(() => {})
    clearSession()
    user.value = null
    initialized.value = true
  }

  return { user, isAuthenticated, initialized, initialize, login, register, fetchUser, logout }
})
