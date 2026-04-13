import api from './client'
import type { Trade } from '@/types'

export async function createTrade(portfolioId: string, assetId: string, action: 'BUY' | 'SELL', quantity: number, rationale?: string) {
  const { data } = await api.post(`/portfolios/${portfolioId}/trades/`, {
    asset_id: assetId,
    action,
    quantity,
    rationale: rationale || 'Manual operation',
  })
  return data
}

export async function getTrades(portfolioId: string): Promise<Trade[]> {
  const { data } = await api.get(`/portfolios/${portfolioId}/trades/`)
  return data.results ?? data
}

export async function getTrade(id: string): Promise<Trade> {
  const { data } = await api.get(`/trades/${id}/`)
  return data
}