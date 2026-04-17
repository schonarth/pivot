import { mount, flushPromises } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import MarketStatusPanel from '../MarketStatusPanel.vue'

vi.mock('@/api/markets', () => ({
  getMarketStatus: vi.fn(),
}))

const { getMarketStatus } = await import('@/api/markets')

describe('MarketStatusPanel', () => {
  beforeEach(() => {
    vi.mocked(getMarketStatus).mockReset()
  })

  it('renders a loading skeleton and then loaded market cards', async () => {
    let resolveStatus: ((value: any) => void) | undefined
    vi.mocked(getMarketStatus).mockImplementation(() => new Promise((resolve) => {
      resolveStatus = resolve
    }))

    const wrapper = mount(MarketStatusPanel, {
      global: {
        stubs: {
          MarketBadge: true,
        },
      },
    })

    expect(wrapper.text()).toContain('Market Status')
    expect(wrapper.findAll('.market-status-skeleton')).toHaveLength(4)
    expect(wrapper.find('.spinner').exists()).toBe(true)

    if (resolveStatus) {
      resolveStatus({
        BR: { open: true },
        US: { open: false },
        UK: { open: true },
        EU: { open: false },
      })
    }

    await flushPromises()

    expect(wrapper.text()).toContain('Open')
    expect(wrapper.text()).toContain('Closed')
  })
})
