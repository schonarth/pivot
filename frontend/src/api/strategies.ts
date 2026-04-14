import api from './client'

export interface StrategyRule {
  id: string
  name: string
  rule_type: string
  description: string
  conditions: Record<string, unknown>
}

export interface StrategyInstance {
  id: string
  portfolio_id: string
  rule_id: string
  rule: StrategyRule
  enabled: boolean
  backtest_approved_at: string | null
  settings: Record<string, unknown>
  created_at: string
}

export interface BacktestScenario {
  id: string
  strategy_instance_id: string
  date_from: string
  date_to: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  result: Record<string, unknown> | null
  error_message: string | null
  created_at: string
  completed_at: string | null
}

export interface StrategyTrade {
  id: string
  strategy_instance_id: string
  asset_id: string
  action: 'BUY' | 'SELL'
  quantity: string
  price: string
  executed_at: string
  auto_executed: boolean
  matched_conditions: Record<string, unknown>
}

export async function getStrategyRules(): Promise<StrategyRule[]> {
  const { data } = await api.get('/strategy-rules/')
  return data.results ?? data
}

export async function getStrategyInstances(portfolioId: string): Promise<StrategyInstance[]> {
  const { data } = await api.get('/strategy-instances/', {
    params: { portfolio_id: portfolioId },
  })
  return data.results ?? data
}

export async function createStrategyInstance(
  portfolioId: string,
  ruleId: string,
  settings: Record<string, unknown>,
): Promise<StrategyInstance> {
  const { data } = await api.post('/strategy-instances/', {
    portfolio_id: portfolioId,
    rule_id: ruleId,
    settings,
  })
  return data
}

export async function updateStrategyInstance(
  strategyId: string,
  payload: Partial<StrategyInstance>,
): Promise<StrategyInstance> {
  const { data } = await api.patch(`/strategy-instances/${strategyId}/`, payload)
  return data
}

export async function runBacktest(
  strategyId: string,
  dateFrom: string,
  dateTo: string,
): Promise<BacktestScenario> {
  const { data } = await api.post(`/strategy-instances/${strategyId}/run_backtest/`, {
    date_from: dateFrom,
    date_to: dateTo,
  })
  return data
}

export async function approveBacktest(strategyId: string): Promise<StrategyInstance> {
  const { data } = await api.post(`/strategy-instances/${strategyId}/approve_backtest/`)
  return data
}

export async function disableStrategy(strategyId: string): Promise<StrategyInstance> {
  const { data } = await api.post(`/strategy-instances/${strategyId}/disable/`)
  return data
}

export async function getBacktests(strategyId: string): Promise<BacktestScenario[]> {
  const { data } = await api.get(`/strategy-instances/${strategyId}/backtests/`)
  return data.results ?? data
}

export async function getStrategyTrades(strategyId: string): Promise<StrategyTrade[]> {
  const { data } = await api.get(`/strategy-instances/${strategyId}/trades/`)
  return data.results ?? data
}

export async function getBacktestScenario(scenarioId: string): Promise<BacktestScenario> {
  const { data } = await api.get(`/backtest-scenarios/${scenarioId}/`)
  return data
}
