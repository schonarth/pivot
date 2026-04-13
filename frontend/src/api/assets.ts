import api from './client'
import type { Asset, AssetQuote, MarketStatus } from '@/types'

export async function searchAssets(q: string, market?: string): Promise<Asset[]> {
  const params: Record<string, string> = { q }
  if (market) params.market = market
  const { data } = await api.get('/assets/', { params })
  return data.results ?? data
}

export async function getAsset(id: string): Promise<Asset> {
  const { data } = await api.get(`/assets/${id}/`)
  return data
}

export async function getAssetPrice(id: string): Promise<AssetQuote> {
  const { data } = await api.get(`/assets/${id}/price/`)
  return data
}

export async function refreshAssetPrice(id: string): Promise<AssetQuote> {
  const { data } = await api.post(`/assets/${id}/refresh-price/`)
  return data
}

export async function getMarketStatus(): Promise<MarketStatus> {
  const { data } = await api.get('/markets/status')
  return data
}

export async function getAssetOHLCV(id: string, days: number = 90): Promise<any[]> {
  const { data } = await api.get(`/assets/${id}/ohlcv/`, { params: { days } })
  return data
}

export async function getAssetIndicators(id: string, days: number = 90): Promise<any[]> {
  const { data } = await api.get(`/assets/${id}/indicators/`, { params: { days } })
  return data
}