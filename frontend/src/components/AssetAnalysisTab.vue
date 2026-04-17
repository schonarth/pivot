<template>
  <div
    v-if="loading"
    class="text-muted"
    style="padding: 2rem; text-align: center;"
  >
    Loading technical data...
  </div>
  <div
    v-else-if="ohlcvData.length === 0"
    class="text-muted"
    style="padding: 2rem; text-align: center;"
  >
    No historical data available for this asset.
  </div>
  <div v-else>
    <div
      class="card"
      style="margin-bottom: 1.5rem;"
    >
      <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; margin-bottom: 1rem;">
        <div>
          <h2 style="margin-bottom: 0.25rem;">
            AI Insight
          </h2>
          <div
            v-if="insight"
            class="text-muted"
            style="font-size: 0.75rem;"
          >
            {{ insight.model_used }} · {{ formatDate(insight.generated_at) }}
          </div>
        </div>
        <button
          class="btn btn-secondary btn-sm"
          :disabled="loadingInsight"
          @click="loadInsight"
        >
          {{ loadingInsight ? 'Generating...' : (insight ? 'Refresh Insight' : 'Generate Insight') }}
        </button>
      </div>

      <div
        v-if="insightError"
        class="text-muted"
      >
        {{ insightError }}
      </div>

      <div v-else-if="insight">
        <div style="display: flex; gap: 0.75rem; flex-wrap: wrap; margin-bottom: 1rem;">
          <span class="badge" :class="recommendationBadgeClass(insight.recommendation)">
            {{ insight.recommendation }}
          </span>
          <span class="badge badge-secondary">
            Confidence {{ insight.confidence }}%
          </span>
          <span
            v-if="insight.price_target !== null"
            class="badge badge-secondary"
          >
            Target {{ insight.price_target }}
          </span>
        </div>

        <p
          v-if="insight.technical_summary"
          style="margin-bottom: 0.75rem; line-height: 1.5;"
        >
          {{ insight.technical_summary }}
        </p>

        <p
          v-if="insight.news_context"
          style="margin-bottom: 1rem; line-height: 1.5;"
        >
          {{ insight.news_context }}
        </p>

        <div v-if="insight.news_items.length">
          <div
            class="text-muted"
            style="font-size: 0.75rem; margin-bottom: 0.5rem;"
          >
            Headlines used
          </div>
          <ul style="margin: 0; padding-left: 1rem;">
            <li
              v-for="item in insight.news_items"
              :key="`${item.source}-${item.headline}`"
              style="margin-bottom: 0.35rem;"
            >
              {{ item.headline }} <span class="text-muted">({{ item.source }})</span>
            </li>
          </ul>
        </div>
      </div>

      <div
        v-else
        class="text-muted"
      >
        Generate an AI view that combines indicators and recent headlines for this asset.
      </div>
    </div>

    <div
      class="card"
      style="margin-bottom: 1.5rem;"
    >
      <h2 style="margin-bottom: 1rem;">
        Technical Analysis
      </h2>

      <div class="chart-panel chart-panel-main">
        <div class="indicator-pills" style="margin-bottom: 0.75rem;">
          <button
            class="indicator-pill"
            :class="{ active: mainIndicator === 'none' }"
            @click="mainIndicator = 'none'"
          >
            None
          </button>
          <button
            class="indicator-pill"
            :class="{ active: mainIndicator === 'mas' }"
            @click="mainIndicator = 'mas'"
          >
            Moving Averages
          </button>
          <button
            class="indicator-pill"
            :class="{ active: mainIndicator === 'bb' }"
            @click="mainIndicator = 'bb'"
          >
            Bollinger Bands
          </button>
        </div>
        <div
          ref="mainChartEl"
          class="chart-container chart-container-main"
        />
      </div>

      <div class="chart-panel chart-panel-oscillator">
        <div
          ref="oscillatorChartEl"
          class="chart-container chart-container-oscillator"
        />
        <div class="indicator-pills" style="margin: 0.5rem 0 0;">
          <button
            class="indicator-pill"
            :class="{ active: oscillatorIndicator === 'rsi' }"
            @click="oscillatorIndicator = 'rsi'"
          >
            RSI (14)
          </button>
          <button
            class="indicator-pill"
            :class="{ active: oscillatorIndicator === 'macd' }"
            @click="oscillatorIndicator = 'macd'"
          >
            MACD
          </button>
        </div>
      </div>
    </div>

    <div class="card">
      <h3 style="margin-bottom: 1rem;">
        Current Indicators
      </h3>
      <div
        v-if="latestIndicators"
        class="grid grid-3"
      >
        <div v-if="latestIndicators.rsi_14 !== null">
          <div
            class="text-muted"
            style="font-size: 0.75rem;"
          >
            RSI (14)
          </div>
          <div style="font-size: 1.25rem; font-weight: 600;">
            {{ Number(latestIndicators.rsi_14).toFixed(2) }}
          </div>
        </div>
        <div v-if="latestIndicators.ma_20 !== null">
          <div
            class="text-muted"
            style="font-size: 0.75rem;"
          >
            MA 20
          </div>
          <div style="font-size: 1.25rem; font-weight: 600;">
            {{ Number(latestIndicators.ma_20).toFixed(4) }}
          </div>
        </div>
        <div v-if="latestIndicators.ma_50 !== null">
          <div
            class="text-muted"
            style="font-size: 0.75rem;"
          >
            MA 50
          </div>
          <div style="font-size: 1.25rem; font-weight: 600;">
            {{ Number(latestIndicators.ma_50).toFixed(4) }}
          </div>
        </div>
        <div v-if="latestIndicators.ma_200 !== null">
          <div
            class="text-muted"
            style="font-size: 0.75rem;"
          >
            MA 200
          </div>
          <div style="font-size: 1.25rem; font-weight: 600;">
            {{ Number(latestIndicators.ma_200).toFixed(4) }}
          </div>
        </div>
        <div v-if="latestIndicators.macd !== null">
          <div
            class="text-muted"
            style="font-size: 0.75rem;"
          >
            MACD
          </div>
          <div style="font-size: 1.25rem; font-weight: 600;">
            {{ Number(latestIndicators.macd).toFixed(4) }}
          </div>
        </div>
        <div v-if="latestIndicators.macd_signal !== null">
          <div
            class="text-muted"
            style="font-size: 0.75rem;"
          >
            Signal
          </div>
          <div style="font-size: 1.25rem; font-weight: 600;">
            {{ Number(latestIndicators.macd_signal).toFixed(4) }}
          </div>
        </div>
      </div>
      <div
        v-else
        class="text-muted"
      >
        No indicator data available.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import ApexCharts from 'apexcharts'
import { getAssetAIInsight, getAssetOHLCV, getAssetIndicators } from '@/api/assets'
import { useNotifications } from '@/composables/useNotifications'
import type { AssetAIInsight } from '@/types'

interface Props {
  assetId: string
}

const props = defineProps<Props>()

const loading = ref(true)
const loadingInsight = ref(false)
const ohlcvData = ref<any[]>([])
const indicatorsData = ref<any[]>([])
const insight = ref<AssetAIInsight | null>(null)
const insightError = ref('')
const mainIndicator = ref<'none' | 'mas' | 'bb'>('mas')
const oscillatorIndicator = ref<'rsi' | 'macd'>('rsi')
const mainChartEl = ref<HTMLDivElement | null>(null)
const oscillatorChartEl = ref<HTMLDivElement | null>(null)
let mainChart: ApexCharts | null = null
let oscillatorChart: ApexCharts | null = null
const chartGroup = 'asset-analysis'

const latestIndicators = computed(() => {
  if (indicatorsData.value.length === 0) return null
  return indicatorsData.value[indicatorsData.value.length - 1]
})

const { showNotification } = useNotifications()

const isDarkMode = () => {
  return localStorage.getItem('theme') === 'dark' ||
    (typeof localStorage === 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches)
}

function hasValidData(data: any[]): boolean {
  return data.some((point) => point.y !== null && point.y !== undefined)
}

function getPriceExtent() {
  const prices = ohlcvData.value.flatMap((d) => [
    Number(d.high),
    Number(d.low),
  ]).filter((value) => Number.isFinite(value) && value > 0)

  if (prices.length === 0) return null

  return {
    min: Math.min(...prices),
    max: Math.max(...prices),
  }
}

function buildLogAxisBounds(minValue: number, maxValue: number) {
  const step = maxValue >= 100 ? 5 : 1
  const min = Math.max(step, Math.floor(minValue / step) * step - step)
  const max = Math.ceil(maxValue / step) * step + step
  const ratio = max / min
  const tickAmount = Math.min(6, Math.max(4, Math.round(Math.log10(ratio) * 12)))

  return {
    min,
    max,
    tickAmount,
  }
}

function buildLogAxisReferenceValues(minValue: number, maxValue: number) {
  if (minValue <= 0 || maxValue <= 0 || maxValue <= minValue) return []

  const ratio = maxValue / minValue
  const count = Math.min(8, Math.max(5, Math.ceil(Math.log10(ratio) * 10)))
  const start = Math.log(minValue)
  const end = Math.log(maxValue)
  const step = (end - start) / (count + 1)

  return Array.from({ length: count }, (_, index) => Math.exp(start + step * (index + 1)))
}

async function loadData() {
  loading.value = true
  try {
    const [ohlcv, indicators] = await Promise.all([
      getAssetOHLCV(props.assetId, 90),
      getAssetIndicators(props.assetId, 90),
    ])
    ohlcvData.value = ohlcv
    indicatorsData.value = indicators
  } catch (error) {
    console.error('Error loading analysis data:', error)
  } finally {
    loading.value = false
  }
}

async function loadInsight() {
  loadingInsight.value = true
  insightError.value = ''
  try {
    insight.value = await getAssetAIInsight(props.assetId)
  } catch (error: any) {
    insight.value = null
    insightError.value = error?.response?.data?.error?.message || 'AI insight is unavailable right now.'
  } finally {
    loadingInsight.value = false
  }
}

function recommendationBadgeClass(recommendation: string): string {
  if (recommendation === 'BUY') return 'badge-success'
  if (recommendation === 'SELL') return 'badge-danger'
  return 'badge-warning'
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString()
}

function destroyCharts() {
  mainChart?.destroy()
  oscillatorChart?.destroy()
  mainChart = null
  oscillatorChart = null
}

function renderMainChart() {
  if (!mainChartEl.value || ohlcvData.value.length === 0) return

  const candlesticks = ohlcvData.value.map((d) => ({
    x: new Date(d.date),
    y: [Number(d.open), Number(d.high), Number(d.low), Number(d.close)],
  }))

  const series: ApexCharts.ApexOptions['series'] = [
    {
      name: 'Candlestick',
      data: candlesticks as any,
    },
  ]

  if (mainIndicator.value === 'mas' && indicatorsData.value.length > 0) {
    series.push({
      name: 'MA 20',
      type: 'line',
      data: indicatorsData.value.map((d) => ({
        x: new Date(d.date),
        y: d.ma_20 !== null ? Number(d.ma_20) : undefined,
      })) as any,
    } as any)
    series.push({
      name: 'MA 50',
      type: 'line',
      data: indicatorsData.value.map((d) => ({
        x: new Date(d.date),
        y: d.ma_50 !== null ? Number(d.ma_50) : undefined,
      })) as any,
    } as any)
    series.push({
      name: 'MA 200',
      type: 'line',
      data: indicatorsData.value.map((d) => ({
        x: new Date(d.date),
        y: d.ma_200 !== null ? Number(d.ma_200) : undefined,
      })) as any,
    } as any)
  } else if (mainIndicator.value === 'bb' && indicatorsData.value.length > 0) {
    series.push({
      name: 'BB Upper',
      type: 'line',
      color: '#16a34a',
      data: indicatorsData.value.map((d) => ({
        x: new Date(d.date),
        y: d.bb_upper !== null ? Number(d.bb_upper) : undefined,
      })) as any,
    } as any)
    series.push({
      name: 'BB Middle',
      type: 'line',
      color: '#f59e0b',
      data: indicatorsData.value.map((d) => ({
        x: new Date(d.date),
        y: d.bb_middle !== null ? Number(d.bb_middle) : undefined,
      })) as any,
    } as any)
    series.push({
      name: 'BB Lower',
      type: 'line',
      color: '#dc2626',
      data: indicatorsData.value.map((d) => ({
        x: new Date(d.date),
        y: d.bb_lower !== null ? Number(d.bb_lower) : undefined,
      })) as any,
    } as any)
  }

  series.forEach((s) => {
    if (s.name !== 'Candlestick' && !hasValidData(s.data as any)) {
      const msg = `No data available for ${s.name}`
      console.warn(msg)
      showNotification('Missing data', { body: msg })
    }
  })

  const darkMode = isDarkMode()
  const textColor = darkMode ? '#e0e0e0' : '#333'
  const gridColor = darkMode ? 'rgba(255, 255, 255, 0.30)' : 'rgba(0, 0, 0, 0.28)'
  const priceExtent = getPriceExtent()
  const logAxis = priceExtent ? buildLogAxisBounds(priceExtent.min, priceExtent.max) : null
  const logMin = logAxis?.min ?? priceExtent?.min ?? 1
  const logMax = logAxis?.max ?? priceExtent?.max ?? 10

  const options: ApexCharts.ApexOptions = {
    chart: {
      type: 'candlestick',
      height: 380,
      animations: { enabled: false },
      background: darkMode ? '#1a1a1a' : '#fff',
      foreColor: textColor,
      group: chartGroup,
      toolbar: {
        show: false,
      },
    },
    xaxis: {
      type: 'datetime',
      labels: {
        show: false,
        style: {
          colors: textColor,
        },
      },
    },
    yaxis: {
      logarithmic: true,
      min: logMin,
      max: logMax,
      tickAmount: logAxis?.tickAmount ?? 4,
      tooltip: {
        enabled: true,
      },
      labels: {
        style: {
          colors: [textColor],
        },
        showDuplicates: false,
        formatter: (value: number) => String(Math.round(value)),
      },
      crosshairs: {
        position: 'back',
      },
    },
    tooltip: {
      theme: darkMode ? 'dark' : 'light',
      x: {
        format: 'dd MMM yyyy',
      },
    },
    grid: {
      borderColor: gridColor,
      position: 'back',
      strokeDashArray: 0,
      xaxis: {
        lines: {
          show: false,
        },
      },
      yaxis: {
        lines: {
          show: true,
        },
      },
    },
    stroke: {
      width: [1, 1, 1, 1],
    },
    dataLabels: {
      enabled: false,
    },
    plotOptions: {
      candlestick: {
        colors: {
          upward: '#16a34a',
          downward: '#dc2626',
        },
        wick: {
          useFillColor: true,
        },
      },
    },
    colors: mainIndicator.value === 'bb'
      ? ['#ffffff', '#16a34a', '#f59e0b', '#dc2626']
      : mainIndicator.value === 'mas'
        ? ['#ffffff', '#93c5fd', '#3b82f6', '#1d4ed8']
        : undefined,
    annotations: logAxis ? {
      yaxis: buildLogAxisReferenceValues(logAxis.min, logAxis.max).map((value) => ({
        y: value,
        borderColor: gridColor,
        strokeDashArray: 1,
      })),
    } : undefined,
  }

  if (mainChart) {
    mainChart.destroy()
  }
  mainChart = new ApexCharts(mainChartEl.value, { ...options, series })
  mainChart.render()
}

function renderOscillatorChart() {
  if (!oscillatorChartEl.value || indicatorsData.value.length === 0) return

  const darkMode = isDarkMode()
  const textColor = darkMode ? '#e0e0e0' : '#333'
  const gridColor = darkMode ? '#333' : '#e0e0e0'

  if (oscillatorIndicator.value === 'rsi') {
    const rsiData = indicatorsData.value.map((d) => ({
      x: new Date(d.date),
      y: d.rsi_14 !== null ? Number(d.rsi_14) : undefined,
    }))

    if (!hasValidData(rsiData as any)) {
      showNotification('Missing data', { body: 'No data available for RSI (14)' })
    }

    const series: ApexCharts.ApexOptions['series'] = [
      {
        name: 'RSI (14)',
        data: rsiData as any,
      },
    ]

    const options: ApexCharts.ApexOptions = {
      chart: {
        type: 'line',
        height: 170,
        animations: { enabled: false },
        background: darkMode ? '#1a1a1a' : '#fff',
        foreColor: textColor,
        group: chartGroup,
        toolbar: {
          show: false,
        },
      },
      xaxis: {
        type: 'datetime',
        labels: {
          style: {
            colors: textColor,
          },
        },
      },
      yaxis: {
        min: 0,
        max: 100,
        tickAmount: 5,
        labels: {
          style: {
            colors: [textColor],
          },
          formatter: (val: number) => Number(val).toFixed(0),
        },
      },
      annotations: {
        yaxis: [
          {
            y: 70,
            borderColor: '#ef4444',
            strokeDashArray: 4,
            label: {
              text: '70',
              style: {
                color: '#ef4444',
                background: 'transparent',
              },
            },
          },
          {
            y: 30,
            borderColor: '#22c55e',
            strokeDashArray: 4,
            label: {
              text: '30',
              style: {
                color: '#22c55e',
                background: 'transparent',
              },
            },
          },
        ],
      },
      legend: {
        show: false,
      },
      stroke: {
        width: 2,
        curve: 'straight',
      },
      colors: ['#3b82f6'],
      tooltip: {
        theme: darkMode ? 'dark' : 'light',
        x: {
          format: 'dd MMM yyyy',
        },
      },
      grid: {
        borderColor: gridColor,
      },
    }

    if (oscillatorChart) {
      oscillatorChart.destroy()
    }
    oscillatorChart = new ApexCharts(oscillatorChartEl.value, { ...options, series })
    oscillatorChart.render()
    return
  }

  const series: ApexCharts.ApexOptions['series'] = [
    {
      name: 'Histogram',
      type: 'bar',
      data: indicatorsData.value.map((d) => ({
        x: new Date(d.date),
        y: d.macd_histogram !== null ? Number(d.macd_histogram) : undefined,
      })) as any,
    },
    {
      name: 'Signal',
      type: 'line',
      data: indicatorsData.value.map((d) => ({
        x: new Date(d.date),
        y: d.macd_signal !== null ? Number(d.macd_signal) : undefined,
      })) as any,
    },
  ]

  series.forEach((s) => {
    if (!hasValidData(s.data as any)) {
      const msg = `No data available for ${s.name}`
      console.warn(msg)
      showNotification('Missing data', { body: msg })
    }
  })

  const options: ApexCharts.ApexOptions = {
    chart: {
      type: 'line',
      height: 170,
      animations: { enabled: false },
      background: darkMode ? '#1a1a1a' : '#fff',
      foreColor: textColor,
      group: chartGroup,
      toolbar: {
        show: false,
      },
    },
    xaxis: {
      type: 'datetime',
      labels: {
        style: {
          colors: textColor,
        },
      },
    },
    yaxis: {
      labels: {
        style: {
          colors: [textColor],
        },
        formatter: (val: number) => Number(val).toFixed(4),
      },
      tooltip: {
        enabled: true,
      },
    },
    annotations: {
      yaxis: [
        {
          y: 0,
          borderColor: gridColor,
          strokeDashArray: 0,
        },
      ],
    },
    legend: {
      show: false,
    },
    stroke: {
      width: [0, 2],
    },
    colors: ['#22c55e', '#3b82f6'],
    plotOptions: {
      bar: {
        columnWidth: '70%',
        colors: {
          ranges: [
            {
              from: -1000000000000,
              to: 0,
              color: '#ef4444',
            },
            {
              from: 0,
              to: 1000000000000,
              color: '#22c55e',
            },
          ],
        },
      },
    },
    tooltip: {
      theme: darkMode ? 'dark' : 'light',
      x: {
        format: 'dd MMM yyyy',
      },
    },
    grid: {
      borderColor: gridColor,
    },
  }

  if (oscillatorChart) {
    oscillatorChart.destroy()
  }
  oscillatorChart = new ApexCharts(oscillatorChartEl.value, { ...options, series })
  oscillatorChart.render()
}

function renderCharts() {
  renderMainChart()
  renderOscillatorChart()
}

watch([mainIndicator, oscillatorIndicator], () => {
  renderCharts()
})

onMounted(() => {
  loadData().then(() => {
    renderCharts()
  })
})

onBeforeUnmount(() => {
  destroyCharts()
})
</script>

<style scoped>
.chart-panel + .chart-panel {
  margin-top: 0.5rem;
}

.chart-container {
  width: 100%;
}

.chart-container-main {
  min-height: 380px;
}

.chart-container-oscillator {
  min-height: 170px;
}

.indicator-pills {
  display: flex;
  gap: 0.25rem;
  align-items: center;
  flex-wrap: wrap;
}

.indicator-pill {
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  border-radius: 9999px;
  padding: 0.35rem 0.75rem;
  font-size: 0.875rem;
  color: var(--text-primary);
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
  white-space: nowrap;
}

.indicator-pill:hover {
  border-color: var(--accent);
}

.indicator-pill.active {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}

:deep(.apexcharts-menu) {
  background-color: var(--surface-secondary, #2a2a2a);
  border-color: var(--border-color, #444);
}

:deep(.apexcharts-menu-item) {
  color: var(--text-primary, #e0e0e0);
}

:deep(.apexcharts-menu-item:hover) {
  background-color: var(--surface-hover, #3a3a3a);
  color: var(--text-primary, #e0e0e0);
}

.chart-panel-main :deep(.apexcharts-legend-series:first-child) {
  display: none !important;
}
</style>
