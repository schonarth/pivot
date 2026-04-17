import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import ScopeInsightCard from '../ScopeInsightCard.vue'
import { flushPromises } from '@vue/test-utils'
import { clearScopeInsightMemory } from '../scopeInsightMemory'

describe('ScopeInsightCard', () => {
  it('defaults collapsed on first mount and reopens from in-memory state later', async () => {
    clearScopeInsightMemory()

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
    expect(wrapper.text()).not.toContain('The monitored set is constructive.')

    await wrapper.find('button').trigger('click')
    await flushPromises()
    await new Promise((resolve) => setTimeout(resolve, 0))
    await flushPromises()

    expect(wrapper.text()).toContain('BUY')
    expect(wrapper.text()).toContain('The monitored set is constructive.')
    expect(wrapper.text()).toContain('Momentum is steady.')
    expect(wrapper.text()).toContain('News remains supportive.')
    expect(wrapper.text()).toContain('gpt-4o-mini')

    wrapper.unmount()

    const remounted = mount(ScopeInsightCard, {
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

    expect(remounted.text()).toContain('BUY')
    expect(remounted.text()).toContain('The monitored set is constructive.')
    expect(remounted.text()).toContain('Momentum is steady.')
    expect(remounted.text()).toContain('News remains supportive.')
    expect(remounted.text()).toContain('gpt-4o-mini')

    remounted.unmount()
  })
})
