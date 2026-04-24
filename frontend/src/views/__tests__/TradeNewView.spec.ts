import { mount, flushPromises } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import TradeNewView from '../TradeNewView.vue'

const push = vi.fn()

vi.mock('@/api/assets', () => ({
  searchAssets: vi.fn(),
  getAssetPrice: vi.fn(),
  getAsset: vi.fn(),
}))

vi.mock('@/api/trades', () => ({
  createTrade: vi.fn(),
}))

vi.mock('@/api/portfolios', () => ({
  getPortfolio: vi.fn(),
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({
    params: { id: 'portfolio-1' },
    query: { asset: 'asset-1' },
  }),
  useRouter: () => ({
    push,
  }),
}))

const { getAssetPrice, getAsset, searchAssets } = await import('@/api/assets')
const { getPortfolio } = await import('@/api/portfolios')

describe('TradeNewView', () => {
  beforeEach(() => {
    vi.mocked(getPortfolio).mockReset()
    vi.mocked(getAsset).mockReset()
    vi.mocked(getAssetPrice).mockReset()
    vi.mocked(searchAssets).mockReset()
    push.mockReset()
  })

  it('shows projected balance and blocks buys that would go negative', async () => {
    vi.mocked(getPortfolio).mockResolvedValue({
      id: 'portfolio-1',
      name: 'Primary',
      market: 'US',
      base_currency: 'USD',
      initial_capital: '1000.00',
      current_cash: '100.00',
      is_primary: true,
      is_simulating: false,
      created_at: '2026-04-16T00:00:00Z',
      updated_at: '2026-04-16T00:00:00Z',
    } as never)
    vi.mocked(getAsset).mockResolvedValue({
      id: 'asset-1',
      display_symbol: 'ALP1',
      name: 'Alpha One',
      market: 'US',
    } as never)
    vi.mocked(getAssetPrice).mockResolvedValue({
      price: '60.00',
      currency: 'USD',
      market_open: true,
    } as never)

    const wrapper = mount(TradeNewView, {
      global: {
        stubs: {
          RouterLink: true,
          MarketBadge: true,
        },
      },
    })

    await flushPromises()

    await wrapper.find('input[type="number"]').setValue(2)
    await flushPromises()

    expect(wrapper.text()).toContain('Balance after transaction:')
    expect(wrapper.text()).toContain('USD -20.00')
    expect(wrapper.find('.negative-balance').exists()).toBe(true)
    expect(wrapper.find('button.btn').attributes('disabled')).toBeDefined()
  })
})
