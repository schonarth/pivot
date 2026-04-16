import api from './client'
import type { User } from '@/types'

export async function register(username: string, email: string, password: string) {
  const { data } = await api.post('/auth/register', { username, email, password })
  return data
}

export async function login(username: string, password: string) {
  const { data } = await api.post('/auth/login', { username, password })
  return data
}

export async function logout() {
  await api.post('/auth/logout')
}

export async function getMe(): Promise<User> {
  const { data } = await api.get('/auth/me')
  return data
}
