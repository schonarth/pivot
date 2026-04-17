<template>
  <div>
    <div class="page-header">
      <h1>Trades</h1>
      <router-link
        :to="`/portfolios/${portfolioId}/trades/new`"
        class="btn"
      >
        New Trade
      </router-link>
    </div>
    <div
      v-if="trades.length"
      class="card"
    >
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Symbol</th>
            <th>Action</th>
            <th>Qty</th>
            <th>Price</th>
            <th>Gross Value</th>
            <th>Fees</th>
            <th>Net Impact</th>
            <th>P&L</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="t in trades"
            :key="t.id"
          >
            <td style="font-size: 0.75rem;">
              {{ formatDate(t.executed_at) }}
            </td>
            <td>{{ t.asset_display_symbol }}</td>
            <td><span :class="t.action === 'BUY' ? 'text-success' : 'text-danger'">{{ t.action }}</span></td>
            <td>{{ t.quantity }}</td>
            <td>{{ Number(t.price).toFixed(4) }}</td>
            <td>{{ Number(t.gross_value).toFixed(2) }}</td>
            <td>{{ Number(t.fees).toFixed(2) }}</td>
            <td :class="Number(t.net_cash_impact) >= 0 ? 'text-success' : 'text-danger'">
              {{ Number(t.net_cash_impact).toFixed(2) }}
            </td>
            <td
              v-if="t.realized_pnl"
              :class="Number(t.realized_pnl) >= 0 ? 'text-success' : 'text-danger'"
            >
              {{ Number(t.realized_pnl).toFixed(2) }}
            </td>
            <td
              v-else
              class="text-muted"
            >
              -
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div
      v-else
      class="card"
    >
      <p class="text-muted">
        No trades yet.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getTrades } from '@/api/trades'
import type { Trade } from '@/types'

const props = defineProps<{ id?: string | string[] }>()
const route = useRoute()
const router = useRouter()

const routePortfolioId = route.params.id as string | string[] | undefined
const propsId = props.id ?? routePortfolioId
const rawId = Array.isArray(propsId) ? propsId[0] : propsId
const portfolioId = rawId ?? ''
const trades = ref<Trade[]>([])

onMounted(async () => {
  if (!portfolioId) {
    await router.replace('/')
    return
  }
  trades.value = await getTrades(portfolioId)
})

function formatDate(d: string): string {
  return new Date(d).toLocaleString()
}
</script>
