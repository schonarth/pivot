import { mount, flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import MarketStatusPanel from '../MarketStatusPanel.vue'

vi.mock('@/api/markets', () => ({
  getMarketStatus: vi.fn(),
}))

const { getMarketStatus } = await import('@/api/markets')

describe('MarketStatusPanel', () => {
  beforeEach(() => {
    vi.mocked(getMarketStatus).mockReset()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders a loading skeleton and refreshes every hour', async () => {
    vi.mocked(getMarketStatus)
      .mockResolvedValueOnce({
        BR: { open: true },
        US: { open: false },
        UK: { open: true },
        EU: { open: false },
      })
      .mockResolvedValueOnce({
        BR: { open: false },
        US: { open: true },
        UK: { open: false },
        EU: { open: true },
      })

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

    await flushPromises()

    expect(wrapper.text()).toContain('Open')
    expect(wrapper.text()).toContain('Closed')
    expect(vi.mocked(getMarketStatus)).toHaveBeenCalledTimes(1)

    await vi.advanceTimersByTimeAsync(60 * 60 * 1000)
    await flushPromises()

    expect(vi.mocked(getMarketStatus)).toHaveBeenCalledTimes(2)
  })
})
