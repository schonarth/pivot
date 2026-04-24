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

vi.mock('@/api/ai', () => ({
  validateStrategyCandidate: vi.fn(),
  getStrategyRecommendations: vi.fn(),
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
const { validateStrategyCandidate, getStrategyRecommendations } = await import('@/api/ai')
const { createTrade } = await import('@/api/trades')

describe('TradeNewView', () => {
  beforeEach(() => {
    vi.mocked(getPortfolio).mockReset()
    vi.mocked(getAsset).mockReset()
    vi.mocked(getAssetPrice).mockReset()
    vi.mocked(searchAssets).mockReset()
    vi.mocked(validateStrategyCandidate).mockReset()
    vi.mocked(getStrategyRecommendations).mockReset()
    vi.mocked(createTrade).mockReset()
    vi.mocked(getStrategyRecommendations).mockResolvedValue([])
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
    expect(validateStrategyCandidate).not.toHaveBeenCalled()
  })

  it('runs strategy validation only from the Should I action and keeps submit separate', async () => {
    vi.mocked(getPortfolio).mockResolvedValue({
      id: 'portfolio-1',
      name: 'Primary',
      market: 'US',
      base_currency: 'USD',
      initial_capital: '1000.00',
      current_cash: '1000.00',
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
    vi.mocked(validateStrategyCandidate).mockResolvedValue({
      id: 'recommendation-1',
      candidate_id: 'candidate-1',
      portfolio: 'portfolio-1',
      asset: 'asset-1',
      asset_display_symbol: 'ALP1',
      asset_name: 'Alpha One',
      action: 'BUY',
      quantity: 1,
      candidate: {},
      technical_inputs: {},
      context_inputs: {},
      sentiment_trajectory_inputs: {},
      divergence_inputs: null,
      verdict: 'reject',
      rationale: 'This trade idea looks weak right now because price momentum is moving against it.',
      recorded_at: '2026-04-16T00:00:00Z',
    } as never)
    vi.mocked(createTrade).mockResolvedValue({} as never)

    const wrapper = mount(TradeNewView, {
      global: {
        stubs: {
          RouterLink: true,
          MarketBadge: true,
        },
      },
    })

    await flushPromises()
    await wrapper.find('input[type="number"]').setValue(1)
    await flushPromises()

    expect(validateStrategyCandidate).not.toHaveBeenCalled()

    await wrapper.findAll('button').find(button => button.text().includes('Should I?'))?.trigger('click')
    await flushPromises()

    expect(validateStrategyCandidate).toHaveBeenCalledWith({
      portfolio_id: 'portfolio-1',
      asset_id: 'asset-1',
      action: 'BUY',
      quantity: 1,
      rationale: undefined,
    })
    expect(wrapper.text()).toContain("Don't")
    expect(wrapper.text()).toContain('This trade idea looks weak right now because price momentum is moving against it.')
    expect(wrapper.text()).not.toContain('Review evidence')
    expect(wrapper.text()).toContain('Previous recommendations')
    expect(wrapper.find('tbody tr[title]').attributes('title')).toContain('This trade idea looks weak')

    await wrapper.findAll('button').find(button => button.text().includes('BUY Trade'))?.trigger('click')
    await flushPromises()

    expect(createTrade).toHaveBeenCalled()
  })
})
