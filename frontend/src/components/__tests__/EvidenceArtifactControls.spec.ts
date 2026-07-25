import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import { nextTick } from 'vue'
import EvidenceArtifactControls from '../EvidenceArtifactControls.vue'

describe('EvidenceArtifactControls', () => {
  it('uses compact bold text controls and a floating stance menu', async () => {
    const wrapper = mount(EvidenceArtifactControls, {
      props: {
        item: {
          news_item_id: 'news-item-1',
          excerpt: 'Headline',
          original_value: 'Headline',
          source_id: 'source-1',
          source_name: 'Source',
          source_stance: null,
          source_stance_controls_enabled: true,
          eligible_source_count: 2,
          current_treatment: { kind: 'baseline', state: null, adjustment: 0 },
          correction_history: [],
          artifact_review_history: [],
          categorical_uncertainty: null,
        },
      },
    })

    const review = wrapper.find('.evidence-review-trigger')
    const stance = wrapper.find('.source-stance-trigger')

    expect(review.text()).toBe('Review')
    expect(stance.text()).toContain('Trust source')
    expect(stance.text()).toContain('⌄')
    expect(review.classes()).not.toContain('btn')
    expect(stance.classes()).not.toContain('btn')

    await stance.trigger('click')

    expect(wrapper.find('.source-stance-options').exists()).toBe(true)
    expect(wrapper.text()).toContain('Do not trust')

    await wrapper.findAll('.source-stance-options button')[1].trigger('click')

    expect(wrapper.find('.source-stance-options').exists()).toBe(false)
    expect(wrapper.emitted('stance')).toEqual([['untrusted']])

    await stance.trigger('click')
    document.body.click()
    await nextTick()

    expect(wrapper.find('.source-stance-options').exists()).toBe(false)
  })
})
