import axios, { type AxiosInstance } from 'axios'
import { getAccessToken, refreshAccessToken, setAuthFailureHandler, setRefreshHandler } from '@/auth/session'

const API_BASE = import.meta.env.VITE_API_URL || ''

const refreshClient = axios.create({
  baseURL: `${API_BASE}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
})

const api: AxiosInstance = axios.create({
  baseURL: `${API_BASE}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
})

api.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

setRefreshHandler(async () => {
  const { data } = await refreshClient.post('/auth/token/refresh')
  return data.access as string
})

setAuthFailureHandler((redirectTo) => {
  const redirect = redirectTo ? `/login?redirect=${encodeURIComponent(redirectTo)}` : '/login'
  window.location.assign(redirect)
})

function isAuthEndpoint(url?: string) {
  if (!url) return false
  return ['/auth/login', '/auth/register', '/auth/token/refresh', '/auth/logout'].some((path) => url.includes(path))
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry && !isAuthEndpoint(originalRequest.url)) {
      originalRequest._retry = true
      const token = await refreshAccessToken()
      if (token) {
        originalRequest.headers = originalRequest.headers || {}
        originalRequest.headers.Authorization = `Bearer ${token}`
        return api(originalRequest)
      }
    }
    return Promise.reject(error)
  },
)

export default api
