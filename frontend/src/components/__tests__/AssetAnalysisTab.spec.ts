import { mount, flushPromises } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import AssetAnalysisTab from '../AssetAnalysisTab.vue'

const apexChartsState = vi.hoisted(() => ({
  instances: [] as Array<{
    options: any
    render: ReturnType<typeof vi.fn>
    destroy: ReturnType<typeof vi.fn>
  }>,
}))

const showNotification = vi.fn()

vi.mock('apexcharts', () => ({
  default: vi.fn().mockImplementation(function (this: any, _el: HTMLElement, options: any) {
    this.options = options
    this.render = vi.fn()
    this.destroy = vi.fn()
    apexChartsState.instances.push(this)
  }),
}))

vi.mock('@/api/assets', () => ({
  getAssetAIInsight: vi.fn(),
  getAssetIndicators: vi.fn(),
  getAssetOHLCV: vi.fn(),
}))

vi.mock('@/composables/useNotifications', () => ({
  useNotifications: () => ({
    showNotification,
  }),
}))

const { getAssetOHLCV, getAssetIndicators, getAssetAIInsight } = await import('@/api/assets')

describe('AssetAnalysisTab', () => {
  beforeEach(() => {
    apexChartsState.instances.length = 0
    showNotification.mockReset()
    vi.mocked(getAssetOHLCV).mockResolvedValue([
      { date: '2025-04-01T00:00:00.000Z', open: '100', high: '110', low: '95', close: '108' },
      { date: '2025-04-02T00:00:00.000Z', open: '108', high: '114', low: '102', close: '111' },
    ])
    vi.mocked(getAssetIndicators).mockResolvedValue([
      {
        date: '2025-04-01T00:00:00.000Z',
        rsi_14: 28.5,
        macd: 1.11,
        macd_signal: 0.95,
        macd_histogram: 0.16,
        ma_20: 102.3,
        ma_50: 99.4,
        ma_200: 95.1,
        bb_upper: 112.2,
        bb_middle: 103.4,
        bb_lower: 94.6,
      },
      {
        date: '2025-04-02T00:00:00.000Z',
        rsi_14: 71.25,
        macd: 1.34,
        macd_signal: 1.02,
        macd_histogram: 0.32,
        ma_20: 103.7,
        ma_50: 99.9,
        ma_200: 95.5,
        bb_upper: 114.1,
        bb_middle: 104.2,
        bb_lower: 94.3,
      },
    ])
    vi.mocked(getAssetAIInsight).mockResolvedValue({
      symbol: 'TEST',
      market: 'US',
      recommendation: 'HOLD',
      confidence: 55,
      technical_summary: 'Technical summary',
      news_context: 'News context',
      reasoning: 'Reasoning',
      price_target: null,
      model_used: 'gpt-test',
      generated_at: '2025-04-02T00:00:00.000Z',
      news_items: [],
    })
  })

  it('renders split chart panels and keeps the price pane logarithmic', async () => {
    const wrapper = mount(AssetAnalysisTab, {
      props: {
        assetId: 'asset-1',
      },
      global: {
        stubs: {
          RouterLink: true,
        },
      },
    })

    await flushPromises()

    const indicatorGroups = wrapper.findAll('.indicator-pills')
    expect(indicatorGroups).toHaveLength(2)
    expect(indicatorGroups[0].text()).toContain('Moving Averages')
    expect(indicatorGroups[0].text()).toContain('Bollinger Bands')
    expect(indicatorGroups[1].text()).toContain('RSI (14)')
    expect(indicatorGroups[1].text()).toContain('MACD')

    expect(wrapper.find('.chart-container-main').exists()).toBe(true)
    expect(wrapper.find('.chart-container-oscillator').exists()).toBe(true)

    expect(apexChartsState.instances).toHaveLength(2)

    const mainChartOptions = apexChartsState.instances[0].options
    const oscillatorChartOptions = apexChartsState.instances[1].options

    expect(mainChartOptions.chart.type).toBe('candlestick')
    expect(mainChartOptions.yaxis.logarithmic).toBe(true)
    expect(mainChartOptions.xaxis.labels.show).toBe(false)
    expect(mainChartOptions.legend).toBeUndefined()
    expect(mainChartOptions.yaxis.min).toBe(90)
    expect(mainChartOptions.yaxis.max).toBe(120)
    expect(mainChartOptions.yaxis.tickAmount).toBe(4)
    expect(mainChartOptions.yaxis.labels.formatter(289.999999999972)).toBe('290')
    expect(mainChartOptions.annotations.yaxis).toHaveLength(5)
    expect(mainChartOptions.grid.position).toBe('back')
    expect(mainChartOptions.grid.yaxis.lines.show).toBe(true)
    expect(mainChartOptions.plotOptions.candlestick.wick.useFillColor).toBe(true)

    expect(oscillatorChartOptions.yaxis.min).toBe(0)
    expect(oscillatorChartOptions.yaxis.max).toBe(100)
    expect(oscillatorChartOptions.annotations.yaxis).toHaveLength(2)
    expect(oscillatorChartOptions.annotations.yaxis[0]).toMatchObject({ y: 70 })
    expect(oscillatorChartOptions.annotations.yaxis[1]).toMatchObject({ y: 30 })
    expect(oscillatorChartOptions.colors).toEqual(['#3b82f6'])
    expect(oscillatorChartOptions.stroke.width).toBe(2)

    await wrapper.findAll('button').find((button) => button.text() === 'MACD')?.trigger('click')
    await flushPromises()

    expect(apexChartsState.instances).toHaveLength(4)
    const latestOscillatorOptions = apexChartsState.instances[3].options
    expect(latestOscillatorOptions.series[0].type).toBe('bar')
    expect(latestOscillatorOptions.series[1].type).toBe('line')
    expect(latestOscillatorOptions.annotations.yaxis[0]).toMatchObject({ y: 0 })
    expect(latestOscillatorOptions.colors).toEqual(['#22c55e', '#3b82f6'])
    expect(latestOscillatorOptions.stroke.width).toEqual([0, 2])

    await wrapper.findAll('button').find((button) => button.text() === 'Bollinger Bands')?.trigger('click')
    await flushPromises()

    expect(apexChartsState.instances).toHaveLength(6)
    const latestMainOptions = apexChartsState.instances[4].options
    expect(latestMainOptions.colors).toEqual(['#ffffff', '#16a34a', '#f59e0b', '#dc2626'])
  })
})
