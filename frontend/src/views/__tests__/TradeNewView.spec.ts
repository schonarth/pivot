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
  getPortfolioSummary: vi.fn(),
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
const { getPortfolio, getPortfolioSummary } = await import('@/api/portfolios')
const { validateStrategyCandidate, getStrategyRecommendations } = await import('@/api/ai')
const { createTrade } = await import('@/api/trades')

describe('TradeNewView', () => {
  beforeEach(() => {
    vi.mocked(getPortfolio).mockReset()
    vi.mocked(getPortfolioSummary).mockReset()
    vi.mocked(getAsset).mockReset()
    vi.mocked(getAssetPrice).mockReset()
    vi.mocked(searchAssets).mockReset()
    vi.mocked(validateStrategyCandidate).mockReset()
    vi.mocked(getStrategyRecommendations).mockReset()
    vi.mocked(createTrade).mockReset()
    vi.mocked(getStrategyRecommendations).mockResolvedValue([])
    vi.mocked(getPortfolioSummary).mockResolvedValue({
      portfolio_id: 'portfolio-1',
      name: 'Primary',
      market: 'US',
      base_currency: 'USD',
      initial_capital: '1000.00',
      current_cash: '1000.00',
      positions_value: '0.00',
      total_equity: '1000.00',
      net_external_cash_flows: '0.00',
      trading_pnl: '0.00',
      is_simulating: false,
      positions: [],
      watch_assets: [],
    } as never)
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

  it('shows current position and blocks sells beyond held quantity', async () => {
    vi.mocked(getPortfolio).mockResolvedValue({
      id: 'portfolio-1',
      name: 'Primary',
      market: 'BR',
      base_currency: 'BRL',
      initial_capital: '1000.00',
      current_cash: '1000.00',
      is_primary: true,
      is_simulating: false,
      created_at: '2026-04-16T00:00:00Z',
      updated_at: '2026-04-16T00:00:00Z',
    } as never)
    vi.mocked(getPortfolioSummary).mockResolvedValue({
      portfolio_id: 'portfolio-1',
      name: 'Primary',
      market: 'BR',
      base_currency: 'BRL',
      initial_capital: '1000.00',
      current_cash: '1000.00',
      positions_value: '936.60',
      total_equity: '1936.60',
      net_external_cash_flows: '0.00',
      trading_pnl: '0.00',
      is_simulating: false,
      positions: [{
        asset_id: 'asset-1',
        symbol: 'PETR4',
        name: 'Petrobras ON',
        quantity: 20,
        average_cost: '40.00',
        current_price: '46.83',
        market_value: '936.60',
        unrealized_pnl: '136.60',
        currency: 'BRL',
      }],
      watch_assets: [],
    } as never)
    vi.mocked(getAsset).mockResolvedValue({
      id: 'asset-1',
      display_symbol: 'PETR4',
      name: 'Petrobras ON',
      market: 'BR',
    } as never)
    vi.mocked(getAssetPrice).mockResolvedValue({
      price: '46.834',
      currency: 'BRL',
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

    expect(wrapper.text()).toContain('PETR4')
    expect(wrapper.text()).toContain('Petrobras ON')
    expect(wrapper.text()).not.toContain('PETR4| Petrobras ON')
    expect(wrapper.text()).toContain('Current Price: BRL 46.83')
    expect(wrapper.text()).toContain('Market Open')
    expect(wrapper.text()).toContain('Current position: 20')
    expect(wrapper.text()).not.toContain('| Current position')

    await wrapper.find('select').setValue('SELL')
    await wrapper.find('input[type="number"]').setValue(21)
    await flushPromises()

    await wrapper.findAll('button').find(button => button.text().includes('SELL Trade'))?.trigger('click')
    await flushPromises()

    expect(wrapper.find('button.btn').attributes('disabled')).toBeDefined()
    expect(createTrade).not.toHaveBeenCalled()
  })

  it('omits zero current position and allows search to replace initial asset', async () => {
    vi.useFakeTimers()
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
    vi.mocked(searchAssets).mockResolvedValue([{
      id: 'asset-2',
      display_symbol: 'BET2',
      name: 'Beta Two',
      market: 'US',
    }] as never)

    const wrapper = mount(TradeNewView, {
      global: {
        stubs: {
          RouterLink: true,
          MarketBadge: true,
        },
      },
    })

    await flushPromises()

    expect(wrapper.text()).toContain('ALP1')
    expect(wrapper.text()).not.toContain('Current position:')

    await wrapper.find('input[type="text"]').setValue('BET')
    await vi.advanceTimersByTimeAsync(300)
    await flushPromises()

    expect(wrapper.text()).not.toContain('Alpha One')
    expect(searchAssets).toHaveBeenCalledWith('BET', 'US')
    expect(wrapper.text()).toContain('BET2')
    expect(wrapper.text()).toContain('Beta Two')

    vi.useRealTimers()
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
