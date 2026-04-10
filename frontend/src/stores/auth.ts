import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { User } from '@/types'
import * as authApi from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const isAuthenticated = ref(!!localStorage.getItem('access_token'))

  async function login(username: string, password: string) {
    const data = await authApi.login(username, password)
    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    user.value = data.user
    isAuthenticated.value = true
  }

  async function register(username: string, email: string, password: string) {
    const data = await authApi.register(username, email, password)
    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    user.value = data.user
    isAuthenticated.value = true
  }

  async function fetchUser() {
    try {
      user.value = await authApi.getMe()
      isAuthenticated.value = true
    } catch {
      logout()
    }
  }

  function logout() {
    const refreshToken = localStorage.getItem('refresh_token')
    if (refreshToken) {
      authApi.logout(refreshToken).catch(() => {})
    }
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    user.value = null
    isAuthenticated.value = false
  }

  return { user, isAuthenticated, login, register, fetchUser, logout }
})