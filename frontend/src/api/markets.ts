import api from './client'
import type { OhlcvBackfillStatus, MarketStatus } from '@/types'

export async function getMarketStatus(): Promise<MarketStatus> {
  const { data } = await api.get('/markets/status/')
  return data
}

export async function getOhlcvBackfillStatus(): Promise<OhlcvBackfillStatus> {
  const { data } = await api.get('/markets/ohlcv-backfill/')
  return data
}

export async function startOhlcvBackfill(): Promise<OhlcvBackfillStatus> {
  const { data } = await api.post('/markets/ohlcv-backfill/')
  return data
}
