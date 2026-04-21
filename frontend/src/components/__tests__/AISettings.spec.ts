import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import AISettings from '../AISettings.vue'

vi.mock('@/api/ai', () => ({
  getSettings: vi.fn(),
  getBudget: vi.fn(),
  setApiKey: vi.fn(),
  removeApiKey: vi.fn(),
  updateSettings: vi.fn(),
  testConnection: vi.fn(),
}))

vi.mock('@/composables/useToast', () => ({
  useToast: () => ({
    error: vi.fn(),
    success: vi.fn(),
  }),
}))

const { getSettings, getBudget, setApiKey } = await import('@/api/ai')

describe('AISettings', () => {
  beforeEach(() => {
    vi.mocked(getSettings).mockResolvedValue({
      provider_name: 'openai',
      enabled: true,
      monthly_budget_usd: 10,
      alert_threshold_pct: 10,
      task_models: {},
      has_api_key: false,
      available_providers: [],
      available_models: {},
      available_tasks: {},
      instance_default_enabled: false,
      instance_default_allow_other_users: false,
      instance_default_owned_by_current_user: false,
      instance_default_owner_username: null,
      can_use_instance_default: false,
    })
    vi.mocked(getBudget).mockResolvedValue({
      enabled: true,
      monthly_budget_usd: '10.00',
      usage_usd: '0.00',
      remaining_usd: '10.00',
      percentage_used: '0',
      at_limit: false,
      should_warn: false,
    })
    vi.mocked(setApiKey).mockResolvedValue(undefined)
  })

  it('keeps a new personal key out of instance-default mode unless explicitly enabled', async () => {
    const wrapper = mount(AISettings)
    await flushPromises()

    const checkboxes = wrapper.findAll('input[type="checkbox"]')
    expect((checkboxes[1].element as HTMLInputElement).checked).toBe(false)

    await wrapper
      .findAll('button')
      .find((button) => button.text() === 'Add Key')
      ?.trigger('click')

    await wrapper.find('input[type="password"]').setValue('test-key')
    await wrapper
      .findAll('button')
      .find((button) => button.text() === 'Save')
      ?.trigger('click')

    expect(setApiKey).toHaveBeenCalledWith('test-key', {
      provider_name: 'openai',
      use_as_instance_default: false,
      allow_other_users: false,
    })
  })
})
