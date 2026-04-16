import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import MonitoredSetAssessment from '../MonitoredSetAssessment.vue'

vi.mock('@/components/AssetAnalysisTab.vue', () => ({
  default: {
    name: 'AssetAnalysisTab',
    template: '<div class="asset-analysis-stub" />',
  },
}))

describe('MonitoredSetAssessment', () => {
  it('renders the monitored set and switches the selected asset', async () => {
    const wrapper = mount(MonitoredSetAssessment, {
      props: {
        title: 'Watch Assessments',
        scopeLabel: 'Portfolio watch',
        emptyMessage: 'No watch assets yet.',
        allowRemoval: true,
        assets: [
          { asset_id: '11111111-1111-1111-1111-111111111111', symbol: 'AAA', name: 'Alpha', market: 'US', currency: 'USD', current_price: '10.00' },
          { asset_id: '22222222-2222-2222-2222-222222222222', symbol: 'BBB', name: 'Beta', market: 'US', currency: 'USD', current_price: null },
        ],
      },
      global: {
        stubs: {
          RouterLink: true,
        },
      },
    })

    expect(wrapper.text()).toContain('Watch Assessments')
    expect(wrapper.text()).toContain('Portfolio watch')
    expect(wrapper.text()).toContain('AAA')
    expect(wrapper.text()).toContain('Remove')
    expect(wrapper.find('.asset-analysis-stub').exists()).toBe(true)

    await wrapper.findAll('button').find((button) => button.text().includes('BBB'))?.trigger('click')

    expect(wrapper.text()).toContain('BBB')

    await wrapper.findAll('button').find((button) => button.text() === 'Remove')?.trigger('click')
    expect(wrapper.emitted('remove')?.[0]).toEqual(['11111111-1111-1111-1111-111111111111'])
  })
})
