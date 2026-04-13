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
      <h2 style="margin-bottom: 1rem;">
        Technical Analysis
      </h2>
      <fieldset style="margin-bottom: 1rem; border: none; padding: 0;">
        <legend style="display: none;">Indicator Selection</legend>
        <div style="display: flex; gap: 1.5rem; flex-wrap: nowrap; overflow-x: auto;">
          <label style="display: flex; align-items: center; gap: 0.5rem; white-space: nowrap;">
            <input
              v-model="selectedIndicator"
              type="radio"
              value="none"
            >
            None
          </label>
          <label style="display: flex; align-items: center; gap: 0.5rem; white-space: nowrap;">
            <input
              v-model="selectedIndicator"
              type="radio"
              value="rsi"
            >
            RSI (14)
          </label>
          <label style="display: flex; align-items: center; gap: 0.5rem; white-space: nowrap;">
            <input
              v-model="selectedIndicator"
              type="radio"
              value="macd"
            >
            MACD
          </label>
          <label style="display: flex; align-items: center; gap: 0.5rem; white-space: nowrap;">
            <input
              v-model="selectedIndicator"
              type="radio"
              value="mas"
            >
            Moving Averages
          </label>
          <label style="display: flex; align-items: center; gap: 0.5rem; white-space: nowrap;">
            <input
              v-model="selectedIndicator"
              type="radio"
              value="bb"
            >
            Bollinger Bands
          </label>
        </div>
      </fieldset>
      <div
        id="candlestick-chart"
        style="height: 400px;"
      />
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
import { ref, computed, onMounted, watch } from 'vue'
import ApexCharts from 'apexcharts'
import { getAssetOHLCV, getAssetIndicators } from '@/api/assets'
import { useNotifications } from '@/composables/useNotifications'

interface Props {
  assetId: string
}

const props = defineProps<Props>()

const loading = ref(true)
const ohlcvData = ref<any[]>([])
const indicatorsData = ref<any[]>([])
const selectedIndicator = ref<'none' | 'rsi' | 'macd' | 'mas' | 'bb'>('mas')
let chart: ApexCharts | null = null

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

function renderChart() {
  if (ohlcvData.value.length === 0) return

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

  const seriesWithSecondaryAxis: any[] = []

  if (selectedIndicator.value === 'mas' && indicatorsData.value.length > 0) {
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
  } else if (selectedIndicator.value === 'bb' && indicatorsData.value.length > 0) {
    series.push({
      name: 'BB Upper',
      type: 'line',
      data: indicatorsData.value.map((d) => ({
        x: new Date(d.date),
        y: d.bb_upper !== null ? Number(d.bb_upper) : undefined,
      })) as any,
    } as any)
    series.push({
      name: 'BB Lower',
      type: 'line',
      data: indicatorsData.value.map((d) => ({
        x: new Date(d.date),
        y: d.bb_lower !== null ? Number(d.bb_lower) : undefined,
      })) as any,
    } as any)
  } else if (selectedIndicator.value === 'rsi' && indicatorsData.value.length > 0) {
    seriesWithSecondaryAxis.push({
      name: 'RSI (14)',
      type: 'line',
      data: indicatorsData.value.map((d) => ({
        x: new Date(d.date),
        y: d.rsi_14 !== null ? Number(d.rsi_14) : undefined,
      })),
    })
  } else if (selectedIndicator.value === 'macd' && indicatorsData.value.length > 0) {
    seriesWithSecondaryAxis.push({
      name: 'MACD',
      type: 'line',
      data: indicatorsData.value.map((d) => ({
        x: new Date(d.date),
        y: d.macd !== null ? Number(d.macd) : undefined,
      })),
    })
    seriesWithSecondaryAxis.push({
      name: 'Signal',
      type: 'line',
      data: indicatorsData.value.map((d) => ({
        x: new Date(d.date),
        y: d.macd_signal !== null ? Number(d.macd_signal) : undefined,
      })),
    })
  }

  series.push(...seriesWithSecondaryAxis)

  series.forEach((s) => {
    if (s.name !== 'Candlestick' && !hasValidData(s.data as any)) {
      const msg = `No data available for ${s.name}`
      console.warn(msg)
      showNotification('Missing data', { body: msg })
    }
  })

  const darkMode = isDarkMode()
  const textColor = darkMode ? '#e0e0e0' : '#333'
  const gridColor = darkMode ? '#333' : '#e0e0e0'

  const hasSecondaryAxis = (selectedIndicator.value === 'rsi' || selectedIndicator.value === 'macd') && indicatorsData.value.length > 0

  // Mark RSI/MACD series to use secondary axis
  if (hasSecondaryAxis) {
    seriesWithSecondaryAxis.forEach((s: any) => {
      s.yAxisIndex = 1
    })
  }

  // Calculate secondary axis range (RSI: 0-100, MACD: centered around 0)
  let secondaryMin: number | undefined
  let secondaryMax: number | undefined
  if (hasSecondaryAxis) {
    if (selectedIndicator.value === 'rsi') {
      secondaryMin = 0
      secondaryMax = 100
    } else if (selectedIndicator.value === 'macd') {
      // Find MACD min/max and create symmetric range
      const macdValues = indicatorsData.value
        .map((d) => d.macd)
        .filter((v) => v !== null && v !== undefined)
        .map((v) => Number(v))
      if (macdValues.length > 0) {
        const absMax = Math.max(...macdValues.map(Math.abs))
        secondaryMin = -absMax * 1.2
        secondaryMax = absMax * 1.2
      }
    }
  }

  const hasSecondaryAxisIndicator = selectedIndicator.value === 'rsi' || selectedIndicator.value === 'macd'

  const options: ApexCharts.ApexOptions = {
    chart: {
      type: 'candlestick',
      height: 400,
      animations: { enabled: false },
      background: darkMode ? '#1a1a1a' : '#fff',
      foreColor: textColor,
    },
    xaxis: {
      type: 'datetime',
      labels: {
        style: {
          colors: textColor,
        },
      },
    },
    yaxis: [
      {
        tooltip: {
          enabled: true,
        },
        labels: {
          style: {
            colors: [textColor],
          },
          formatter: (val: number) => Number(val).toFixed(0),
        },
      },
      ...(hasSecondaryAxisIndicator ? [{
        opposite: true,
        min: secondaryMin,
        max: secondaryMax,
        tooltip: {
          enabled: true,
        },
        labels: {
          style: {
            colors: [textColor],
          },
          formatter: (val: number) => Number(val).toFixed(0),
        },
        title: {
          text: selectedIndicator.value === 'rsi' ? 'RSI' : 'MACD',
          style: {
            color: textColor,
          },
        },
      }] : []),
    ] as any,
    legend: {
      position: 'bottom',
      horizontalAlign: 'center',
      fontSize: '12',
      labels: {
        colors: textColor,
      },
      itemMargin: {
        horizontal: 8,
        vertical: 4,
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

  const container = document.getElementById('candlestick-chart')
  if (container) {
    if (chart) {
      chart.destroy()
    }
    chart = new ApexCharts(container, { ...options, series })
    chart.render()
  }
}

watch(selectedIndicator, () => {
  renderChart()
})

onMounted(() => {
  loadData().then(() => {
    renderChart()
  })
})
</script>

<style scoped>
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
</style>
