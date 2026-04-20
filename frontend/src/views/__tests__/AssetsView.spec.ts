import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'
import AssetsView from '../AssetsView.vue'

const { searchAssets, lookupAssetSymbol } = vi.hoisted(() => ({
  searchAssets: vi.fn(),
  lookupAssetSymbol: vi.fn(),
}))

vi.mock('@/api/assets', () => ({
  searchAssets,
  lookupAssetSymbol,
}))

vi.mock('@/components/MarketBadge.vue', () => ({
  default: {
    name: 'MarketBadge',
    props: ['market'],
    template: '<span>{{ market }}</span>',
  },
}))

describe('AssetsView', () => {
  beforeEach(() => {
    searchAssets.mockReset()
    lookupAssetSymbol.mockReset()
    vi.useFakeTimers()
    vi.stubGlobal('ResizeObserver', class {
      observe() {}
      disconnect() {}
    })
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
  })

  it('falls back to exact lookup when the local search returns nothing', async () => {
    searchAssets.mockResolvedValueOnce([])
    searchAssets.mockResolvedValueOnce([])
    lookupAssetSymbol.mockResolvedValueOnce([
      {
        id: 'asset-1',
        figi: null,
        display_symbol: 'ALP1',
        provider_symbol: 'ALP1.SA',
        name: 'Alpha One',
        market: 'BR',
        exchange: 'BVMF',
        currency: 'BRL',
        sector: null,
        industry: null,
        is_seeded: false,
        created_at: '2026-04-16T00:00:00Z',
      },
    ])

    const wrapper = mount(AssetsView)

    await flushPromises()
    await vi.advanceTimersByTimeAsync(300)
    await flushPromises()

    await wrapper.find('input').setValue('ALP1')
    await vi.advanceTimersByTimeAsync(300)
    await flushPromises()

    expect(searchAssets).toHaveBeenNthCalledWith(1, '', undefined)
    expect(searchAssets).toHaveBeenNthCalledWith(2, 'ALP1', undefined)
    expect(lookupAssetSymbol).toHaveBeenCalledWith('ALP1', undefined)
    expect(wrapper.text()).toContain('ALP1')
    expect(wrapper.text()).toContain('Alpha One')
  })
})
