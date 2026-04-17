import { mount, flushPromises } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import PortfolioCard from '../PortfolioCard.vue'

const push = vi.fn()

vi.mock('@/api/portfolios', () => ({
  getPortfolioSummary: vi.fn(),
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push,
  }),
}))

const { getPortfolioSummary } = await import('@/api/portfolios')

describe('PortfolioCard', () => {
  beforeEach(() => {
    vi.mocked(getPortfolioSummary).mockReset()
    push.mockReset()
  })

  it('renders basic portfolio data immediately and fills equity summary later', async () => {
    let resolveSummary: ((value: any) => void) | undefined
    vi.mocked(getPortfolioSummary).mockImplementation(() => new Promise((resolve) => {
      resolveSummary = resolve
    }))

    const wrapper = mount(PortfolioCard, {
      props: {
        portfolio: {
          id: 'portfolio-1',
          name: 'Growth',
          market: 'US',
          base_currency: 'USD',
          initial_capital: '10000.00',
          current_cash: '2500.00',
          is_primary: true,
          is_simulating: false,
          created_at: '2026-04-16T00:00:00Z',
          updated_at: '2026-04-16T00:00:00Z',
        },
      },
      global: {
        stubs: {
          MarketBadge: true,
        },
      },
    })

    expect(wrapper.text()).toContain('Growth')
    expect(wrapper.text()).toContain('Cash')
    expect(wrapper.text()).toContain('USD 2,500.00')
    expect(wrapper.find('.portfolio-card-skeleton').exists()).toBe(true)

    if (resolveSummary) {
      resolveSummary({
        portfolio_id: 'portfolio-1',
        name: 'Growth',
        market: 'US',
        base_currency: 'USD',
        initial_capital: '10000.00',
        current_cash: '2500.00',
        positions_value: '7500.00',
        total_equity: '10000.00',
        net_external_cash_flows: '0.00',
        trading_pnl: '120.00',
        is_simulating: false,
        positions: [],
        watch_assets: [],
      })
    }

    await flushPromises()

    expect(wrapper.text()).toContain('Total Equity')
    expect(wrapper.text()).toContain('USD 10,000.00')
    expect(wrapper.text()).toContain('Invested')
    expect(wrapper.text()).toContain('USD 7,500.00')
    expect(wrapper.text()).toContain('Trading P&L')
    expect(wrapper.text()).toContain('USD 120.00')
  })
})
