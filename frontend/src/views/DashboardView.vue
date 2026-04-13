<template>
  <div>
    <div class="page-header">
      <h1>Dashboard</h1>
      <router-link to="/portfolios/new" class="btn">New Portfolio</router-link>
    </div>

    <div v-if="loading" style="text-align: center; padding: 2rem;"><span class="spinner"></span></div>

    <template v-else>
      <div v-if="summaries.length" class="grid grid-4" style="margin-bottom: 1.5rem;">
        <div class="card">
          <div class="text-muted" style="font-size: 0.75rem;">Total Equity</div>
          <div style="font-size: 1.25rem; font-weight: 600;">
            {{ totalCurrency }} {{ formatNum(totalEquity) }}
          </div>
        </div>
        <div class="card">
          <div class="text-muted" style="font-size: 0.75rem;">Total Cash</div>
          <div style="font-size: 1.25rem; font-weight: 600;">
            {{ totalCurrency }} {{ formatNum(totalCash) }}
          </div>
        </div>
        <div class="card">
          <div class="text-muted" style="font-size: 0.75rem;">Invested</div>
          <div style="font-size: 1.25rem; font-weight: 600;">
            {{ totalCurrency }} {{ formatNum(totalInvested) }}
          </div>
        </div>
        <div class="card">
          <div class="text-muted" style="font-size: 0.75rem;">Trading P&L</div>
          <div :class="Number(totalPnl) >= 0 ? 'text-success' : 'text-danger'" style="font-size: 1.25rem; font-weight: 600;">
            {{ totalCurrency }} {{ formatNum(totalPnl) }}
          </div>
        </div>
      </div>

      <h2 style="margin-bottom: 1rem;">Portfolios</h2>
      <div v-if="validPortfolios.length" class="grid grid-3">
        <div v-for="p in validPortfolios" :key="p.id" class="card portfolio-card" :style="p.is_simulating ? { backgroundColor: 'rgba(255, 193, 7, 0.05)' } : {}" @click="$router.push(`/portfolios/${p.id}`)">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <strong>{{ p.name }}</strong>
            <MarketBadge :market="p.market" />
          </div>
          <div style="display: flex; justify-content: space-between;">
            <span class="text-muted">Cash</span>
            <span>{{ p.base_currency }} {{ formatNum(p.current_cash) }}</span>
          </div>
          <div style="display: flex; justify-content: space-between;">
            <span class="text-muted">Capital</span>
            <span>{{ p.base_currency }} {{ formatNum(p.initial_capital) }}</span>
          </div>
          <div style="display: flex; gap: 0.5rem; margin-top: 0.25rem;">
            <div v-if="p.is_primary">
              <span class="badge badge-success">Primary</span>
            </div>
            <div v-if="p.is_simulating">
              <span class="badge badge-warning">Simulating</span>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="card">
        <p class="text-muted">No portfolios yet. Create one to get started!</p>
      </div>

      <div v-if="summaries.length" style="margin-top: 2rem;">
        <h2 style="margin-bottom: 1rem;">Market Status</h2>
        <div class="grid grid-4">
          <div v-for="(status, market) in marketStatus" :key="market" class="card">
            <span class="badge" :class="status.open ? 'badge-success' : 'badge-warning'" style="margin-right: 0.5rem;">
              {{ status.open ? 'Open' : 'Closed' }}
            </span>
            <strong>{{ market }}</strong>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import MarketBadge from '@/components/MarketBadge.vue'
import { usePortfolioStore } from '@/stores/portfolios'
import { useMarketStore } from '@/stores/markets'
import { getPortfolioSummary } from '@/api/portfolios'
import { formatCurrency } from '@/utils/numbers'
import { storeToRefs } from 'pinia'
import type { PortfolioSummary } from '@/types'

const portfolioStore = usePortfolioStore()
const marketStore = useMarketStore()
const { portfolios } = storeToRefs(portfolioStore)
const validPortfolios = computed(() => portfolios.value.filter((p) => Boolean(p.id) && p.id !== 'undefined'))
const { status: marketStatus } = storeToRefs(marketStore)

const loading = ref(true)
const summaries = ref<PortfolioSummary[]>([])

onMounted(async () => {
  await portfolioStore.fetchPortfolios()
  try {
    await marketStore.fetchStatus()
  } catch { /* market status unavailable */ }
  for (const p of validPortfolios.value) {
    try {
      const s = await getPortfolioSummary(p.id)
      summaries.value.push(s)
    } catch { /* skip failing portfolios */ }
  }
  loading.value = false
})

const totalEquity = computed(() => summaries.value.reduce((sum, s) => sum + Number(s.total_equity), 0))
const totalCash = computed(() => summaries.value.reduce((sum, s) => sum + Number(s.current_cash), 0))
const totalInvested = computed(() => summaries.value.reduce((sum, s) => sum + Number(s.positions_value), 0))
const totalPnl = computed(() => summaries.value.reduce((sum, s) => sum + Number(s.trading_pnl), 0))
const totalCurrency = computed(() => summaries.value[0]?.base_currency || 'USD')

function formatNum(val: string | number, currency?: string): string {
  return formatCurrency(val, currency)
}
</script>

<style scoped>
.portfolio-card {
  cursor: pointer;
  transition: transform 0.15s;
}
.portfolio-card:hover {
  transform: translateY(-2px);
}
</style>
