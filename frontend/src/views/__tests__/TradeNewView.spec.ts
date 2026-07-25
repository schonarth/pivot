import { mount, flushPromises } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import TradeNewView from '../TradeNewView.vue'

const push = vi.fn()
const routeQuery: Record<string, string> = { asset: 'asset-1' }

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
  getRecommendationEvidence: vi.fn(),
  createFactCorrection: vi.fn(),
  createArtifactReview: vi.fn(),
  setSourceStance: vi.fn(),
  clearSourceStance: vi.fn(),
}))

vi.mock('@/api/portfolios', () => ({
  getPortfolio: vi.fn(),
  getPortfolioSummary: vi.fn(),
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({
    params: { id: 'portfolio-1' },
    query: routeQuery,
  }),
  useRouter: () => ({
    push,
  }),
}))

const { getAssetPrice, getAsset, searchAssets } = await import('@/api/assets')
const { getPortfolio, getPortfolioSummary } = await import('@/api/portfolios')
const { validateStrategyCandidate, getStrategyRecommendations, getRecommendationEvidence } = await import('@/api/ai')
const { createTrade } = await import('@/api/trades')

describe('TradeNewView', () => {
  beforeEach(() => {
    delete routeQuery.evidenceSourceStanceOverride
    vi.mocked(getPortfolio).mockReset()
    vi.mocked(getPortfolioSummary).mockReset()
    vi.mocked(getAsset).mockReset()
    vi.mocked(getAssetPrice).mockReset()
    vi.mocked(searchAssets).mockReset()
    vi.mocked(validateStrategyCandidate).mockReset()
    vi.mocked(getStrategyRecommendations).mockReset()
    vi.mocked(getRecommendationEvidence).mockReset()
    vi.mocked(createTrade).mockReset()
    vi.mocked(getStrategyRecommendations).mockResolvedValue([])
    vi.mocked(getRecommendationEvidence).mockResolvedValue({ evidence: [], fact_key_suggestions: [] })
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
      context_inputs: {
        items: [{
          headline: 'Alpha One faces selling pressure',
        }],
      },
      sentiment_trajectory_inputs: {},
      divergence_inputs: null,
      verdict: 'reject',
      rationale: 'This trade looks weak right now because price momentum is moving against it.',
      scenario_frames: [
        {
          id: 'scenario-1',
          scenario_case: 'base',
          direction: 'conditional',
          catalysts: [{ source: 'technical_inputs', text: 'Technical vote: negative' }],
          invalidating_conditions: [{ source: 'context_inputs', text: 'Context improves' }],
          confidence_band: 'low',
          risk_notes: 'Alpha One faces selling pressure . Skip it unless the setup improves clearly.',
          position_size_guidance: 'Treat the candidate as advisory under current guardrails.',
          generated_at: '2026-04-16T00:00:00Z',
        },
        {
          id: 'scenario-2',
          scenario_case: 'bull',
          direction: 'supportive',
          catalysts: [],
          invalidating_conditions: [],
          confidence_band: 'medium',
          risk_notes: 'Asset upside would support this trade.',
          position_size_guidance: 'Keep sizing modest.',
          generated_at: '2026-04-16T00:00:00Z',
        },
        {
          id: 'scenario-3',
          scenario_case: 'bear',
          direction: 'adverse',
          catalysts: [],
          invalidating_conditions: [],
          confidence_band: 'medium',
          risk_notes: 'Asset downside would work against this trade.',
          position_size_guidance: 'Keep sizing modest.',
          generated_at: '2026-04-16T00:00:00Z',
        },
      ],
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
    expect(wrapper.text()).toContain('This trade looks weak right now because price momentum is moving against it.')
    expect(wrapper.text()).toContain('Scenarios')
    expect(wrapper.text()).toContain('Base case')
    expect(wrapper.text()).toContain('conditional for BUY')
    expect(wrapper.text()).toContain('Bull case')
    expect(wrapper.text()).toContain('supportive for BUY')
    expect(wrapper.text()).toContain('Bear case')
    expect(wrapper.text()).toContain('adverse for BUY')
    expect(wrapper.text()).toContain('Alpha One faces selling pressure')
    expect(wrapper.find('.scenario-evidence').text()).toBe('Context improves')
    expect(wrapper.find('.scenario-frame p em').text()).toBe('Alpha One faces selling pressure.')
    expect(wrapper.find('.scenario-frame p').text()).not.toContain('pressure .')
    expect(wrapper.text()).not.toContain('Technical vote: negative')
    expect(wrapper.text()).not.toContain('Treat the candidate as advisory')
    expect(wrapper.text()).toContain('Evidence review')
    expect(wrapper.text()).toContain('Previous recommendations')

    await wrapper.find('.recommendation-toggle').trigger('click')
    await flushPromises()

    expect(wrapper.find('.recommendation-detail-row').text()).toContain('This trade looks weak')
    expect(wrapper.find('.recommendation-detail-row').text()).toContain('Alpha One faces selling pressure')
    expect(wrapper.find('.recommendation-detail-row').text()).toContain('Bull case')
    expect(wrapper.find('.recommendation-detail-row').text()).toContain('supportive for BUY')
    expect(wrapper.find('.recommendation-detail-row').text()).not.toContain('Technical vote: negative')

    const scenarioTitles = wrapper.findAll('.scenario-frame-header strong').map(item => item.text())
    expect(scenarioTitles.slice(0, 3)).toEqual(['Bull case', 'Base case', 'Bear case'])

    await wrapper.findAll('button').find(button => button.text().includes('BUY Trade'))?.trigger('click')
    await flushPromises()

    expect(createTrade).toHaveBeenCalled()
  })

  it('frames sell validation scenarios relative to the trade action', async () => {
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
      id: 'recommendation-sell-1',
      candidate_id: 'candidate-1',
      portfolio: 'portfolio-1',
      asset: 'asset-1',
      asset_display_symbol: 'ALP1',
      asset_name: 'Alpha One',
      action: 'SELL',
      quantity: 1,
      candidate: {},
      technical_inputs: {},
      context_inputs: {},
      sentiment_trajectory_inputs: {},
      divergence_inputs: null,
      verdict: 'defer',
      rationale: 'The sell trade needs clearer confirmation.',
      scenario_frames: [
        {
          id: 'scenario-sell-1',
          scenario_case: 'bull',
          direction: 'adverse',
          catalysts: [],
          invalidating_conditions: [],
          confidence_band: 'medium',
          risk_notes: 'Asset upside would work against this sell trade.',
          position_size_guidance: 'Keep sizing modest.',
          generated_at: '2026-04-16T00:00:00Z',
        },
        {
          id: 'scenario-sell-2',
          scenario_case: 'bear',
          direction: 'supportive',
          catalysts: [],
          invalidating_conditions: [],
          confidence_band: 'medium',
          risk_notes: 'Asset downside would support this sell trade.',
          position_size_guidance: 'Keep sizing modest.',
          generated_at: '2026-04-16T00:00:00Z',
        },
      ],
      recorded_at: '2026-04-16T00:00:00Z',
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
    await wrapper.find('select').setValue('SELL')
    await wrapper.find('input[type="number"]').setValue(1)
    await flushPromises()

    await wrapper.findAll('button').find(button => button.text().includes('Should I?'))?.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Bull case')
    expect(wrapper.text()).toContain('adverse for SELL')
    expect(wrapper.text()).toContain('Bear case')
    expect(wrapper.text()).toContain('supportive for SELL')
    expect(wrapper.text()).toContain('Asset upside would work against this sell trade.')
    expect(wrapper.text()).toContain('Asset downside would support this sell trade.')
    expect(wrapper.text()).not.toContain('supportive for BUY')
    expect(wrapper.text()).not.toContain('adverse for BUY')
  })

  it('renders stored recommendation scenario frames with their stored trade action', async () => {
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
    vi.mocked(getStrategyRecommendations).mockResolvedValue([{
      id: 'stored-recommendation-1',
      candidate_id: 'candidate-1',
      portfolio: 'portfolio-1',
      asset: 'asset-1',
      asset_display_symbol: 'ALP1',
      asset_name: 'Alpha One',
      action: 'SELL',
      quantity: 2,
      candidate: {},
      technical_inputs: {},
      context_inputs: {},
      sentiment_trajectory_inputs: {},
      divergence_inputs: null,
      verdict: 'approve',
      rationale: 'Stored sell recommendation.',
      scenario_frames: [
        {
          id: 'stored-scenario-1',
          scenario_case: 'bull',
          direction: 'adverse',
          catalysts: [],
          invalidating_conditions: [],
          confidence_band: 'high',
          risk_notes: 'Stored bullish case is adverse to the sell.',
          position_size_guidance: 'Keep sizing modest.',
          generated_at: '2026-04-16T00:00:00Z',
        },
      ],
      recorded_at: '2026-04-16T00:00:00Z',
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
    await wrapper.find('.recommendation-toggle').trigger('click')
    await flushPromises()

    expect(wrapper.find('.recommendation-detail-row').text()).toContain('Stored sell recommendation.')
    expect(wrapper.find('.recommendation-detail-row').text()).toContain('Bull case')
    expect(wrapper.find('.recommendation-detail-row').text()).toContain('adverse for SELL')
    expect(wrapper.find('.recommendation-detail-row').text()).toContain('Stored bullish case is adverse to the sell.')
  })

  it('keeps original evidence read-only, normalizes fact keys, and leaves stance disabled with one eligible source', async () => {
    vi.mocked(getStrategyRecommendations).mockResolvedValue([{
      id: 'evidence-recommendation', candidate_id: 'candidate', portfolio: 'portfolio-1', asset: 'asset-1', asset_display_symbol: 'ALP1', asset_name: 'Alpha One', action: 'BUY', quantity: 1,
      candidate: {}, technical_inputs: {}, context_inputs: {}, sentiment_trajectory_inputs: {}, divergence_inputs: null,
      verdict: 'defer', rationale: 'Evidence review.', scenario_frames: [], recorded_at: '2026-04-16T00:00:00Z',
    }] as never)
    vi.mocked(getRecommendationEvidence).mockResolvedValue({
      fact_key_suggestions: ['earnings_result'],
      evidence: [{
        news_item_id: 'news-1', excerpt: 'Alpha reports earnings', original_value: 'Alpha reports earnings', source_id: 'source-1', source_name: 'Source', source_stance: null,
        eligible_source_count: 1, source_stance_controls_enabled: false, current_treatment: { kind: 'baseline', state: null, adjustment: 0 }, correction_history: [], artifact_review_history: [], categorical_uncertainty: null,
      }],
    })

    const wrapper = mount(TradeNewView, { global: { stubs: { RouterLink: true, MarketBadge: true } } })
    await flushPromises()
    await wrapper.find('.recommendation-toggle').trigger('click')
    await flushPromises()

    expect(wrapper.find('.evidence-review input').exists()).toBe(false)
    await wrapper.find('.evidence-review-trigger').trigger('click')
    const original = wrapper.find('.evidence-review-modal input[readonly]')
    expect(original.element).toHaveProperty('readOnly', true)
    const factKey = wrapper.find('.evidence-review-modal input[list]')
    await factKey.setValue('Earnings Result!')
    await factKey.trigger('blur')
    expect((factKey.element as HTMLInputElement).value).toBe('earnings_result')
    expect(wrapper.find('.source-stance-trigger').attributes('disabled')).toBeDefined()
    expect(wrapper.text()).toContain('Source stance requires at least two eligible configured sources.')
  })

  it('requests the development override so enabled source-stance controls remain testable', async () => {
    routeQuery.evidenceSourceStanceOverride = 'true'
    vi.mocked(getStrategyRecommendations).mockResolvedValue([{
      id: 'override-recommendation', candidate_id: 'candidate', portfolio: 'portfolio-1', asset: 'asset-1', asset_display_symbol: 'ALP1', asset_name: 'Alpha One', action: 'BUY', quantity: 1,
      candidate: {}, technical_inputs: {}, context_inputs: {}, sentiment_trajectory_inputs: {}, divergence_inputs: null,
      verdict: 'defer', rationale: 'Evidence review.', scenario_frames: [], recorded_at: '2026-04-16T00:00:00Z',
    }] as never)
    vi.mocked(getRecommendationEvidence).mockResolvedValue({
      fact_key_suggestions: [],
      evidence: [{
        news_item_id: 'news-1', excerpt: 'Alpha reports earnings', original_value: 'Alpha reports earnings', source_id: 'source-1', source_name: 'Source', source_stance: null,
        eligible_source_count: 1, source_stance_controls_enabled: true, current_treatment: { kind: 'baseline', state: null, adjustment: 0 }, correction_history: [], artifact_review_history: [], categorical_uncertainty: null,
      }],
    })

    const wrapper = mount(TradeNewView, { global: { stubs: { RouterLink: true, MarketBadge: true } } })
    await flushPromises()
    await wrapper.find('.recommendation-toggle').trigger('click')
    await flushPromises()

    expect(getRecommendationEvidence).toHaveBeenCalledWith('override-recommendation', true)
    expect(wrapper.find('.source-stance-trigger').attributes('disabled')).toBeUndefined()
  })
})
