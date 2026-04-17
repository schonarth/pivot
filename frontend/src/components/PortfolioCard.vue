<template>
  <div
    class="card portfolio-card"
    :style="portfolio.is_simulating ? { backgroundColor: 'rgba(255, 193, 7, 0.05)' } : {}"
    @click="goToDetail"
  >
    <div style="display: flex; justify-content: space-between; align-items: center; gap: 0.75rem; margin-bottom: 0.75rem;">
      <strong>{{ portfolio.name }}</strong>
      <MarketBadge :market="portfolio.market" />
    </div>

    <div style="display: flex; justify-content: space-between;">
      <span class="text-muted">Cash</span>
      <span>{{ portfolio.base_currency }} {{ formatNum(portfolio.current_cash) }}</span>
    </div>
    <div style="display: flex; justify-content: space-between;">
      <span class="text-muted">Capital</span>
      <span>{{ portfolio.base_currency }} {{ formatNum(portfolio.initial_capital) }}</span>
    </div>

    <div
      v-if="portfolio.is_primary || portfolio.is_simulating"
      style="display: flex; gap: 0.5rem; margin-top: 0.5rem;"
    >
      <span
        v-if="portfolio.is_primary"
        class="badge badge-success"
      >
        Primary
      </span>
      <span
        v-if="portfolio.is_simulating"
        class="badge badge-warning"
      >
        Simulating
      </span>
    </div>

    <div class="portfolio-card-equity">
      <div
        v-if="loading"
        class="portfolio-card-skeleton"
      >
        <div class="portfolio-card-skeleton-row" />
        <div class="portfolio-card-skeleton-row" />
        <div class="portfolio-card-skeleton-row" />
      </div>

      <div
        v-else-if="summary"
        class="portfolio-card-equity-grid"
      >
        <div>
          <div class="text-muted" style="font-size: 0.75rem;">
            Total Equity
          </div>
          <div style="font-weight: 600;">
            {{ summary.base_currency }} {{ formatNum(summary.total_equity) }}
          </div>
        </div>
        <div>
          <div class="text-muted" style="font-size: 0.75rem;">
            Invested
          </div>
          <div style="font-weight: 600;">
            {{ summary.base_currency }} {{ formatNum(summary.positions_value) }}
          </div>
        </div>
        <div>
          <div class="text-muted" style="font-size: 0.75rem;">
            Trading P&L
          </div>
          <div
            :class="Number(summary.trading_pnl) >= 0 ? 'text-success' : 'text-danger'"
            style="font-weight: 600;"
          >
            {{ summary.base_currency }} {{ formatNum(summary.trading_pnl) }}
          </div>
        </div>
      </div>

      <div
        v-else
        class="text-muted"
        style="font-size: 0.85rem;"
      >
        Equity summary unavailable.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import MarketBadge from '@/components/MarketBadge.vue'
import { getPortfolioSummary } from '@/api/portfolios'
import { formatCurrency } from '@/utils/numbers'
import type { Portfolio, PortfolioSummary } from '@/types'

const props = defineProps<{
  portfolio: Portfolio
}>()

const router = useRouter()
const summary = ref<PortfolioSummary | null>(null)
const loading = ref(true)

onMounted(async () => {
  try {
    summary.value = await getPortfolioSummary(props.portfolio.id)
  } catch {
    summary.value = null
  } finally {
    loading.value = false
  }
})

function goToDetail() {
  void router.push(`/portfolios/${props.portfolio.id}`)
}

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

.portfolio-card-equity {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--border);
}

.portfolio-card-equity-grid {
  display: grid;
  gap: 0.5rem;
}

.portfolio-card-skeleton {
  display: grid;
  gap: 0.55rem;
}

.portfolio-card-skeleton-row {
  height: 0.9rem;
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(148, 163, 184, 0.15), rgba(148, 163, 184, 0.28), rgba(148, 163, 184, 0.15));
  background-size: 200% 100%;
  animation: portfolio-card-shimmer 1.2s ease-in-out infinite;
}

@keyframes portfolio-card-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
