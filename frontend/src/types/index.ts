export interface User {
  id: string
  api_uuid: string
  username: string
  email: string
  first_name: string
  last_name: string
}

export interface AuthTokens {
  access: string
  refresh: string
}

export interface Portfolio {
  id: string
  name: string
  market: string
  base_currency: string
  initial_capital: string
  current_cash: string
  is_primary: boolean
  is_simulating: boolean
  created_at: string
  updated_at: string
}

export interface PortfolioSummary {
  portfolio_id: string
  name: string
  market: string
  base_currency: string
  initial_capital: string
  current_cash: string
  positions_value: string
  total_equity: string
  net_external_cash_flows: string
  trading_pnl: string
  is_simulating: boolean
  positions: PositionDetail[]
  watch_assets: MonitoredAssetSummary[]
  scope_insights?: PortfolioScopeInsights
}

export interface PositionDetail {
  asset_id: string
  symbol: string
  name: string
  quantity: number
  average_cost: string
  current_price: string
  market_value: string
  unrealized_pnl: string
  currency: string
}

export interface MonitoredScopeInsight {
  scope_type: 'portfolio' | 'watch'
  scope_label: string
  asset_count: number
  recommendation: 'BUY' | 'HOLD' | 'SELL'
  confidence: number
  summary: string
  technical_summary: string
  news_context: string
  reasoning: string
  sentiment_trajectory?: SentimentTrajectory | null
  divergence_analysis?: DivergenceAnalysis | null
  divergence_summary?: string
  divergence_disclosure?: string
  model_used: string
  generated_at: string
}

export interface PortfolioScopeInsights {
  portfolio: MonitoredScopeInsight | null
  watch: MonitoredScopeInsight | null
}

export interface MonitoredAssetSummary {
  asset_id: string
  symbol: string
  name: string
  market: string
  currency: string
  current_price: string | null
}

export interface Trade {
  id: string
  portfolio: string
  asset: string
  asset_display_symbol: string
  action: 'BUY' | 'SELL'
  quantity: number
  price: string
  gross_value: string
  fees: string
  net_cash_impact: string
  realized_pnl: string | null
  rationale: string
  executed_by: string
  executed_at: string
}

export interface Asset {
  id: string
  figi: string | null
  display_symbol: string
  provider_symbol: string
  name: string
  market: string
  exchange: string
  currency: string
  sector: string | null
  industry: string | null
  is_seeded: boolean
  created_at: string
}

export interface AssetQuote {
  id: string
  asset: string
  asset_symbol: string
  price: string
  currency: string
  source: string
  as_of: string
  fetched_at: string
  is_delayed: boolean
  market_open?: boolean
  stale?: boolean
}

export interface AssetAIInsightNewsItem {
  headline: string
  url?: string
  source: string
  published_at: string | null
  bucket?: 'symbol' | 'company' | 'sector' | 'industry' | 'macro' | 'theme'
  provenance?: string
  relevance_basis?: string
  asset_symbol?: string | null
  market?: string | null
}

export interface SentimentTrajectoryEntry {
  subject_type: 'asset' | 'theme'
  subject: string
  state: 'improving' | 'deteriorating' | 'conflicting' | 'reversal'
  summary: string
  evidence_count: number
}

export interface SentimentTrajectory {
  entries: SentimentTrajectoryEntry[]
}

export interface DivergenceAnalysis {
  label: 'no_divergence' | 'insufficient_signal' | 'no_material_follow_through' | 'competing_macro_priority' | 'reversal' | 'uncertainty_conflict'
  expected_direction: 'up' | 'down' | 'none'
  actual_direction: 'up' | 'down' | 'flat'
  actual_percent_move: string
  flat_threshold_percent: string
  signal_votes: {
    technical: 'positive' | 'negative' | 'neutral'
    context: 'positive' | 'negative' | 'neutral'
    trajectory: 'positive' | 'negative' | 'neutral'
    shared_context: 'positive' | 'negative' | 'neutral'
  }
  macro_confirmation: boolean
}

export interface AssetAIInsight {
  symbol: string
  market: string
  recommendation: 'BUY' | 'HOLD' | 'SELL'
  confidence: number
  summary: string
  technical_summary: string
  news_context: string
  reasoning: string
  price_target: number | null
  sentiment_trajectory?: SentimentTrajectory | null
  divergence_analysis?: DivergenceAnalysis | null
  divergence_summary?: string
  divergence_disclosure?: string
  model_used: string
  generated_at: string
  news_items: AssetAIInsightNewsItem[]
}

export interface StrategyRecommendation {
  id: string
  candidate_id: string
  portfolio: string
  asset: string
  asset_display_symbol: string
  asset_name: string
  action: 'BUY' | 'SELL'
  quantity: number
  candidate: Record<string, unknown>
  technical_inputs: Record<string, unknown>
  context_inputs: Record<string, unknown>
  sentiment_trajectory_inputs: Record<string, unknown>
  divergence_inputs: Record<string, unknown> | null
  verdict: 'approve' | 'reject' | 'defer'
  rationale: string
  recorded_at: string
}

export interface AlertTriggerTrade {
  action: 'BUY' | 'SELL'
  quantity: number
  price: string
  gross_value: string
  fees: string
  net_cash_impact: string
}

export interface AlertLatestTrigger {
  id: string
  triggered_price: string
  triggered_at: string
  outcome: string
  notification_sent: boolean
  price_was_override: boolean
  trade: AlertTriggerTrade | null
}

export interface Alert {
  id: string
  portfolio: string
  asset: string
  asset_display_symbol: string
  condition_type: 'price_above' | 'price_below'
  threshold: string
  notify_enabled: boolean
  auto_trade_enabled: boolean
  auto_trade_side: 'BUY' | 'SELL' | null
  auto_trade_quantity: number | null
  auto_trade_pct: string | null
  status: 'active' | 'triggered' | 'paused'
  last_evaluated_at: string | null
  triggered_at: string | null
  latest_trigger: AlertLatestTrigger | null
  created_at: string
  updated_at: string
}

export interface TimelineEvent {
  id: string
  portfolio: string
  event_type: string
  description: string
  metadata: Record<string, unknown>
  created_at: string
}

export interface CashTransaction {
  id: string
  transaction_type: 'initial_funding' | 'deposit' | 'withdrawal'
  amount: string
  resulting_cash: string
  created_at: string
}

export interface MarketStatus {
  [key: string]: { open: boolean }
}

export interface OhlcvBackfillProcessedAsset {
  symbol: string
  status: 'completed' | 'failed'
  rows_ingested?: number
  error?: string
  timestamp: string
}

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

export interface OhlcvBackfillStatus {
  state: 'idle' | 'queued' | 'running' | 'completed' | 'failed'
  source: string | null
  initiated_by: string | null
  total_assets: number
  processed_assets_count: number
  successful_assets: number
  failed_assets: number
  current_asset: {
    symbol: string
    index: number
    total_assets: number
  } | null
  processed_assets: OhlcvBackfillProcessedAsset[]
  started_at: string | null
  updated_at: string
  completed_at: string | null
  queued?: boolean
}

export interface OhlcvRepairProcessedAsset {
  symbol: string
  status: 'completed' | 'failed'
  invalid_rows_deleted?: number
  rows_ingested?: number
  error?: string
  timestamp: string
}

export interface OhlcvRepairStatus {
  state: 'idle' | 'queued' | 'running' | 'completed' | 'failed'
  source: string | null
  initiated_by: string | null
  symbol: string | null
  date_from: string | null
  date_to: string | null
  total_assets: number
  processed_assets_count: number
  invalid_rows_found: number
  invalid_rows_deleted: number
  repaired_rows: number
  current_asset: {
    symbol: string
    index: number
    total_assets: number
  } | null
  processed_assets: OhlcvRepairProcessedAsset[]
  started_at: string | null
  updated_at: string
  completed_at: string | null
  queued?: boolean
}

export interface WSMessage {
  type: string
  [key: string]: unknown
}
