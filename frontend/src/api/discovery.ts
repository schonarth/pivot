import api from './client'

export interface DiscoveryShortlistItem {
  asset_id: string
  symbol: string
  market: string
  rank: number
  score: string
  score_breakdown: {
    technical_setup: number
    breakout: number
    context_support: number
    freshness: number
  }
  technical_signals: Record<string, unknown>
  context_summary: Record<string, unknown>
  discovery_reason: string
  watch_action_ready: boolean
  refined_reason?: string | null
}

export interface DiscoveryResult {
  market: string
  universe_size: number
  survivor_count: number
  shortlist_count: number
  shortlist: DiscoveryShortlistItem[]
  refinement: {
    requested: boolean
    applied: boolean
    cache_hit: boolean
    fingerprint: string | null
  }
  generated_at: string
}

export async function getDiscovery(market: string, options?: { refine?: boolean; refresh?: boolean }): Promise<DiscoveryResult> {
  const params: Record<string, string> = { market }
  if (options?.refine) params.refine = 'true'
  if (options?.refresh) params.refresh = 'true'
  const { data } = await api.get('/ai/discovery/', { params })
  return data
}
