import client from './client'

export interface AISettings {
  provider_name: string
  monthly_budget_usd: number
  alert_threshold_pct: number
  task_models: Record<string, string>
  has_api_key: boolean
  available_providers: Array<{ value: string; label: string }>
  available_models: Record<string, string[]>
  available_tasks: Record<string, Record<string, string>>
  instance_default_enabled: boolean
  instance_default_allow_other_users: boolean
  instance_default_owned_by_current_user: boolean
  instance_default_owner_username: string | null
  can_use_instance_default: boolean
}

export interface AIBudget {
  enabled: boolean
  monthly_budget_usd: string
  usage_usd: string
  remaining_usd: string
  percentage_used: string
  at_limit: boolean
  should_warn: boolean
}

export async function getSettings(): Promise<AISettings> {
  const response = await client.get('/ai/get_settings/')
  return response.data
}

export async function getBudget(): Promise<AIBudget> {
  const response = await client.get('/ai/budget/')
  return response.data
}

export async function setApiKey(
  apiKey: string,
  options?: {
    provider_name?: string
    use_as_instance_default?: boolean
    allow_other_users?: boolean
  },
): Promise<void> {
  await client.post('/ai/set_api_key/', {
    api_key: apiKey,
    ...options,
  })
}

export async function removeApiKey(): Promise<void> {
  await client.post('/ai/remove_api_key/', {})
}

export async function updateSettings(settings: Partial<AISettings>): Promise<AISettings> {
  const response = await client.post('/ai/update_settings/', settings)
  return response.data
}

export async function testConnection(provider_name?: string, api_key?: string): Promise<{ status: string; provider: string; model: string; message: string }> {
  const response = await client.post('/ai/test_connection/', { provider_name, api_key })
  return response.data
}
