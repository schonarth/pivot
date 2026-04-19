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
          sentiment_trajectory: {
            entries: [
              {
                subject_type: 'asset',
                subject: 'AAA',
                state: 'improving',
                summary: 'Asset AAA is turning more positive across 3 retained items.',
                evidence_count: 3,
              },
            ],
          },
          divergence_analysis: {
            label: 'competing_macro_priority',
            expected_direction: 'up',
            actual_direction: 'down',
            actual_percent_move: '-0.0321',
            flat_threshold_percent: '0.005',
            signal_votes: {
              technical: 'positive',
              context: 'positive',
              trajectory: 'positive',
              shared_context: 'negative',
            },
            macro_confirmation: true,
          },
          divergence_summary: 'Expected up, but broader context matched the opposite move.',
          divergence_disclosure: 'Broader-force labels only appear when explicit monitored-set or shared-context evidence exists.',
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
    expect(wrapper.text()).toContain('Sentiment trajectory')
    expect(wrapper.text()).toContain('Divergence')
    expect(wrapper.text()).toContain('Macro won')
    expect(wrapper.text()).toContain('NO MATCH')
    expect(wrapper.text()).toContain('Expected up, but broader context matched the opposite move.')
    expect(wrapper.text()).toContain('Broader-force labels only appear when explicit monitored-set or shared-context evidence exists.')
    expect(wrapper.text()).toContain('Sentiment trajectory')
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
          sentiment_trajectory: {
            entries: [
              {
                subject_type: 'asset',
                subject: 'AAA',
                state: 'improving',
                summary: 'Asset AAA is turning more positive across 3 retained items.',
                evidence_count: 3,
              },
            ],
          },
          divergence_analysis: {
            label: 'competing_macro_priority',
            expected_direction: 'up',
            actual_direction: 'down',
            actual_percent_move: '-0.0321',
            flat_threshold_percent: '0.005',
            signal_votes: {
              technical: 'positive',
              context: 'positive',
              trajectory: 'positive',
              shared_context: 'negative',
            },
            macro_confirmation: true,
          },
          divergence_summary: 'Expected up, but broader context matched the opposite move.',
          divergence_disclosure: 'Broader-force labels only appear when explicit monitored-set or shared-context evidence exists.',
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
    expect(remounted.text()).toContain('Sentiment trajectory')
    expect(remounted.text()).toContain('Divergence')
    expect(remounted.text()).toContain('Macro won')
    expect(remounted.text()).toContain('Sentiment trajectory')
    expect(remounted.text()).toContain('News remains supportive.')
    expect(remounted.text()).toContain('gpt-4o-mini')

    remounted.unmount()
  })
})
