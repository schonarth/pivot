import api from './client'
import type { Alert } from '@/types'

export async function getAlerts(portfolioId: string): Promise<Alert[]> {
  const { data } = await api.get(`/portfolios/${portfolioId}/alerts/`)
  return data.results ?? data
}

export async function createAlert(
  portfolioId: string,
  payload: {
    asset_id: string
    condition_type: 'price_above' | 'price_below'
    threshold: string
    notify_enabled: boolean
    auto_trade_enabled: boolean
    auto_trade_side?: string
    auto_trade_quantity?: number
    auto_trade_pct?: string
  },
): Promise<Alert> {
  const { data } = await api.post(`/portfolios/${portfolioId}/alerts/`, payload)
  return data
}

export async function updateAlert(id: string, payload: Partial<Alert>): Promise<Alert> {
  const { data } = await api.put(`/alerts/${id}/`, payload)
  return data
}

export async function deleteAlert(id: string): Promise<void> {
  await api.delete(`/alerts/${id}/`)
}

export async function pauseAlert(id: string): Promise<Alert> {
  const { data } = await api.post(`/alerts/${id}/pause/`)
  return data
}

export async function resumeAlert(id: string): Promise<Alert> {
  const { data } = await api.post(`/alerts/${id}/resume/`)
  return data
}