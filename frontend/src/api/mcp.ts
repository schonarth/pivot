import api from './client'

export interface MCPAgent {
  id: string
  name: string
  origin: string
  created_at: string
}

export interface OTPResponse {
  code: string
  expires_at: string
}

export async function generateOTP(): Promise<OTPResponse> {
  const { data } = await api.post('/mcp/otp/generate/')
  return data
}

export async function exchangeOTPForToken(userID: string, code: string, name?: string, origin?: string) {
  const { data } = await api.post('/mcp/token/exchange/', {
    user_id: userID,
    otp: code,
    name: name || 'Unknown Agent',
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
