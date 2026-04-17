import api from './client'
import type { MarketStatus, OhlcvBackfillStatus, OhlcvRepairStatus } from '@/types'

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

export async function getOhlcvRepairStatus(): Promise<OhlcvRepairStatus> {
  const { data } = await api.get('/markets/ohlcv-repair/')
  return data
}

export async function startOhlcvRepair(payload: {
  symbol?: string | null
  date_from?: string | null
  date_to?: string | null
}): Promise<OhlcvRepairStatus> {
  const { data } = await api.post('/markets/ohlcv-repair/', payload)
  return data
}
