import { mount, flushPromises } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import DiscoveryView from '../DiscoveryView.vue'

const push = vi.fn()

vi.mock('@/api/discovery', () => ({
  getDiscovery: vi.fn(),
}))

vi.mock('@/api/ai', () => ({
  getSettings: vi.fn(),
}))

vi.mock('@/api/portfolios', () => ({
  getPortfolios: vi.fn(),
  addPortfolioWatchAsset: vi.fn(),
}))

vi.mock('@/composables/useToast', () => ({
  useToast: () => ({
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
  }),
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push,
  }),
}))

const { getDiscovery } = await import('@/api/discovery')
const { getSettings } = await import('@/api/ai')
const { getPortfolios, addPortfolioWatchAsset } = await import('@/api/portfolios')

describe('DiscoveryView', () => {
  beforeEach(() => {
    vi.mocked(getDiscovery).mockReset()
    vi.mocked(getSettings).mockReset()
    vi.mocked(getPortfolios).mockReset()
    vi.mocked(addPortfolioWatchAsset).mockReset()
    push.mockReset()
  })

  it('loads a refined shortlist when AI access is available and can add a watch asset', async () => {
    vi.mocked(getSettings).mockResolvedValue({
      enabled: true,
      has_api_key: true,
      can_use_instance_default: false,
    } as never)
    vi.mocked(getPortfolios).mockResolvedValue([
      {
        id: 'portfolio-1',
        name: 'Primary',
        market: 'US',
        base_currency: 'USD',
        initial_capital: '10000.00',
        current_cash: '10000.00',
        is_primary: true,
        is_simulating: false,
        created_at: '2026-04-16T00:00:00Z',
        updated_at: '2026-04-16T00:00:00Z',
      },
    ] as never)
    vi.mocked(getDiscovery).mockResolvedValue({
      market: 'US',
      universe_size: 1,
      survivor_count: 1,
      shortlist_count: 1,
      shortlist: [
        {
          asset_id: 'asset-1',
          symbol: 'ALP1',
          market: 'US',
          rank: 1,
          score: '8',
          score_breakdown: {
            technical_setup: 3,
            breakout: 3,
            context_support: 1,
            freshness: 1,
          },
          technical_signals: {
            liquidity_floor_met: true,
            trend_intact: true,
            breakout_confirmed: true,
          },
          context_summary: {
            item_count: 1,
            support: 'positive',
            trajectory: 'improving',
          },
          discovery_reason: 'Deterministic reason.',
          watch_action_ready: true,
          refined_reason: 'Refined reason.',
        },
      ],
      refinement: {
        requested: true,
        applied: true,
        cache_hit: false,
        fingerprint: 'abc123',
      },
      generated_at: '2026-04-16T00:00:00Z',
    } as never)

    const wrapper = mount(DiscoveryView, {
      global: {
        stubs: {
          RouterLink: true,
        },
      },
    })

    await flushPromises()

    expect(vi.mocked(getDiscovery)).toHaveBeenCalledWith('US', { refine: true, refresh: false })
    expect(wrapper.text()).toContain('Refined reason.')

    const watchButton = wrapper.findAll('button').find((button) => button.text() === 'Watch')
    expect(watchButton).toBeTruthy()

    await watchButton!.trigger('click')
    await flushPromises()

    expect(vi.mocked(addPortfolioWatchAsset)).toHaveBeenCalledWith('portfolio-1', 'asset-1')
    expect(push).toHaveBeenCalledWith({ path: '/portfolios/portfolio-1', query: { tab: 'watch' } })
  })

  it('loads deterministic discovery when AI access is unavailable', async () => {
    vi.mocked(getSettings).mockResolvedValue({
      enabled: true,
      has_api_key: false,
      can_use_instance_default: false,
    } as never)
    vi.mocked(getPortfolios).mockResolvedValue([] as never)
    vi.mocked(getDiscovery).mockResolvedValue({
      market: 'US',
      universe_size: 1,
      survivor_count: 1,
      shortlist_count: 1,
      shortlist: [],
      refinement: {
        requested: false,
        applied: false,
        cache_hit: false,
        fingerprint: null,
      },
      generated_at: '2026-04-16T00:00:00Z',
    } as never)

    const wrapper = mount(DiscoveryView, {
      global: {
        stubs: {
          RouterLink: true,
        },
      },
    })

    await flushPromises()

    expect(vi.mocked(getDiscovery)).toHaveBeenCalledWith('US', { refine: false, refresh: false })
    expect(wrapper.text()).toContain('Deterministic shortlist loaded.')
  })
})
