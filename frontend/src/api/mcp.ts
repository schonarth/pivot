import api from './client'

export interface MCPAgent {
  id: string
  name: string
  origin: string
  llm_provider: string
  llm_model: string
  created_at: string
}

export interface OTPResponse {
  code: string
  expires_at: string
}

export interface MCPEndpoint {
  name: string
  method: string
  path: string
  description: string
  auth: string
  params: Array<{
    name: string
    type: string
    required?: boolean
    description?: string
    location?: string
  }>
  response: Record<string, string> | Record<string, string>[]
}

export interface MCPSchema {
  version: string
  base_url: string
  authentication: Record<string, string>
  endpoints: MCPEndpoint[]
  caching: Record<string, string>
}

export async function getSchema(): Promise<MCPSchema> {
  const { data } = await api.get('/mcp/schema/')
  return data
}

export async function generateOTP(): Promise<OTPResponse> {
  const { data } = await api.post('/mcp/otp/generate/')
  return data
}

export async function exchangeOTPForToken(
  userID: string,
  code: string,
  name: string,
  llmProvider: string,
  llmModel: string,
  origin?: string,
) {
  const { data } = await api.post('/mcp/token/exchange/', {
    user_id: userID,
    otp: code,
    name,
    llm_provider: llmProvider,
    llm_model: llmModel,
    origin: origin || 'unknown',
  })
  return data
}

export async function listAgents(): Promise<MCPAgent[]> {
  const { data } = await api.get('/mcp/agents/')
  return data
}

export async function revokeAgent(agentID: string) {
  await api.delete(`/mcp/agents/${agentID}/`)
}

export async function getAssetInsight(agentToken: string, assetId: string) {
  const { data } = await api.post('/mcp/asset-insight/', {
    agent_token: agentToken,
    asset_id: assetId,
  })
  return data
}

export async function lookupAssetSymbol(agentToken: string, symbol: string, market?: string) {
  const { data } = await api.post('/mcp/assets/lookup-symbol/', {
    agent_token: agentToken,
    symbol,
    market,
  })
  return data
}

export async function getAISettings(agentToken: string) {
  const { data } = await api.get('/mcp/ai-settings/', {
    params: { agent_token: agentToken },
  })
  return data
}

export async function listStrategyRules(agentToken: string) {
  const { data } = await api.get('/mcp/strategy-rules/', {
    params: { agent_token: agentToken },
  })
  return data
}

export async function listStrategyInstances(agentToken: string) {
  const { data } = await api.get('/mcp/strategy-instances/', {
    params: { agent_token: agentToken },
  })
  return data
}

export async function listStrategyTrades(agentToken: string) {
  const { data } = await api.get('/mcp/strategy-trades/', {
    params: { agent_token: agentToken },
  })
  return data
}

export async function listAgentTrades(agentToken: string) {
  const { data } = await api.get('/mcp/agent-trades/', {
    params: { agent_token: agentToken },
  })
  return data
}

export async function createBacktest(agentToken: string, strategyInstanceId: string, dateFrom: string, dateTo: string) {
  const { data } = await api.post('/mcp/backtest/create/', {
    agent_token: agentToken,
    strategy_instance_id: strategyInstanceId,
    date_from: dateFrom,
    date_to: dateTo,
  })
  return data
}

export async function getBacktestResults(agentToken: string, backtestId: string) {
  const { data } = await api.get(`/mcp/backtest/${backtestId}/results/`, {
    params: { agent_token: agentToken },
  })
  return data
}
