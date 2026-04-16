import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import ScopeInsightCard from '../ScopeInsightCard.vue'

describe('ScopeInsightCard', () => {
  it('renders the scope insight summary and fallback state', async () => {
    const wrapper = mount(ScopeInsightCard, {
      props: {
        title: 'Portfolio AI Summary',
        scopeLabel: 'Portfolio positions',
        assetCount: 2,
        emptyMessage: 'No positions to analyze yet.',
        insight: {
          scope_type: 'portfolio',
          scope_label: 'Portfolio positions',
          asset_count: 2,
          recommendation: 'BUY',
          confidence: 84,
          summary: 'The monitored set is constructive.',
          technical_summary: 'Momentum is steady.',
          news_context: 'News remains supportive.',
          reasoning: 'The monitored set is constructive.',
          model_used: 'gpt-4o-mini',
          generated_at: '2026-04-16T00:00:00Z',
        },
      },
    })

    expect(wrapper.text()).toContain('Portfolio AI Summary')
    expect(wrapper.text()).toContain('Portfolio positions')
    expect(wrapper.text()).toContain('BUY')
    expect(wrapper.text()).toContain('The monitored set is constructive.')
    expect(wrapper.text()).toContain('gpt-4o-mini')

    await wrapper.setProps({ insight: null })

    expect(wrapper.text()).toContain('No positions to analyze yet.')
  })
})
