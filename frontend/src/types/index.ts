export interface User {
  id: string
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
  positions: PositionDetail[]
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

export interface WSMessage {
  type: string
  [key: string]: unknown
}