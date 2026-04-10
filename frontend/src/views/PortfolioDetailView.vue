<template>
  <div v-if="summary">
    <div class="page-header">
      <h1>{{ summary.name }}</h1>
      <div style="display: flex; gap: 0.5rem;">
        <button class="btn btn-secondary btn-sm" @click="handleRefresh" :disabled="refreshing">Refresh Prices</button>
        <button class="btn btn-secondary btn-sm" @click="showDeposit = true">Deposit</button>
        <button class="btn btn-secondary btn-sm" @click="showWithdraw = true">Withdraw</button>
        <router-link :to="`/portfolios/${portfolioId}/trades/new`" class="btn btn-sm">New Trade</router-link>
      </div>
    </div>
    <div class="grid grid-4">
      <div class="card">
        <div class="text-muted" style="font-size: 0.75rem;">Total Equity</div>
        <div style="font-size: 1.25rem; font-weight: 600;">{{ summary.base_currency }} {{ formatNum(summary.total_equity) }}</div>
      </div>
      <div class="card">
        <div class="text-muted" style="font-size: 0.75rem;">Cash</div>
        <div style="font-size: 1.25rem; font-weight: 600;">{{ summary.base_currency }} {{ formatNum(summary.current_cash) }}</div>
      </div>
      <div class="card">
        <div class="text-muted" style="font-size: 0.75rem;">Invested</div>
        <div style="font-size: 1.25rem; font-weight: 600;">{{ summary.base_currency }} {{ formatNum(summary.positions_value) }}</div>
      </div>
      <div class="card">
        <div class="text-muted" style="font-size: 0.75rem;">Trading P&L</div>
        <div :class="Number(summary.trading_pnl) >= 0 ? 'text-success' : 'text-danger'" style="font-size: 1.25rem; font-weight: 600;">
          {{ summary.base_currency }} {{ formatNum(summary.trading_pnl) }}
        </div>
      </div>
    </div>
    <div class="grid grid-2" style="margin-top: 1rem;">
      <div class="card">
        <div class="text-muted" style="font-size: 0.75rem;">Net Deposits/Withdrawals</div>
        <div style="font-size: 1rem;">{{ summary.base_currency }} {{ formatNum(summary.net_external_cash_flows) }}</div>
      </div>
      <div class="card">
        <div class="text-muted" style="font-size: 0.75rem;">Market</div>
        <span class="badge badge-info">{{ summary.market }}</span>
      </div>
    </div>

    <h2 style="margin-top: 2rem; margin-bottom: 1rem;">Positions</h2>
    <div class="card" v-if="summary.positions.length">
      <table>
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Qty</th>
            <th>Avg Cost</th>
            <th>Current Price</th>
            <th>Market Value</th>
            <th>Unrealized P&L</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="pos in summary.positions" :key="pos.asset_id">
            <td><router-link :to="`/assets/${pos.asset_id}`">{{ pos.symbol }}</router-link></td>
            <td>{{ pos.quantity }}</td>
            <td>{{ formatNum(pos.average_cost) }}</td>
            <td>{{ formatNum(pos.current_price) }}</td>
            <td>{{ formatNum(pos.market_value) }}</td>
            <td :class="Number(pos.unrealized_pnl) >= 0 ? 'text-success' : 'text-danger'">
              {{ formatNum(pos.unrealized_pnl) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="card">
      <p class="text-muted">No positions yet. Start by making a trade!</p>
    </div>

    <h2 style="margin-top: 2rem; margin-bottom: 1rem;">Recent Activity</h2>
    <div v-if="timeline.length" class="card">
      <div v-for="event in timeline.slice(0, 10)" :key="event.id" style="padding: 0.5rem 0; border-bottom: 1px solid var(--border);">
        <div style="display: flex; justify-content: space-between;">
          <span>{{ event.description }}</span>
          <span class="text-muted" style="font-size: 0.75rem;">{{ formatDate(event.created_at) }}</span>
        </div>
      </div>
    </div>
    <div v-else class="card"><p class="text-muted">No activity yet.</p></div>

    <div v-if="showDeposit" class="modal-overlay" @click.self="showDeposit = false">
      <div class="card modal-content">
        <h3>Deposit</h3>
        <div class="form-group">
          <label>Amount</label>
          <input ref="depositInput" v-model="depositAmount" type="text" inputmode="decimal" placeholder="0.00" @keyup.enter="handleDeposit" />
        </div>
        <div style="display: flex; gap: 0.5rem; justify-content: flex-end;">
          <button class="btn btn-secondary" @click="showDeposit = false">Cancel</button>
          <button class="btn btn-success" @click="handleDeposit">Deposit</button>
        </div>
      </div>
    </div>

    <div v-if="showWithdraw" class="modal-overlay" @click.self="showWithdraw = false">
      <div class="card modal-content">
        <h3>Withdraw</h3>
        <div v-if="withdrawWarning" class="alert-danger">{{ withdrawWarning }}</div>
        <div class="form-group">
          <label>Amount</label>
          <input ref="withdrawInput" v-model="withdrawAmount" type="text" inputmode="decimal" placeholder="0.00" @keyup.enter="handleWithdraw" />
        </div>
        <div style="display: flex; gap: 0.5rem; justify-content: flex-end;">
          <button class="btn btn-secondary" @click="showWithdraw = false">Cancel</button>
          <button class="btn btn-danger" @click="handleWithdraw">Withdraw</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getPortfolioSummary, getPortfolioTimeline, refreshPortfolioPrices, deposit, withdraw } from '@/api/portfolios'
import { parseNumericInput, formatCurrency } from '@/utils/numbers'
import type { PortfolioSummary } from '@/types'

const props = defineProps<{ id?: string | string[] }>()
const route = useRoute()
const router = useRouter()

const routePortfolioId = route.params.id as string | string[] | undefined
const propsId = props.id ?? routePortfolioId
const rawId = Array.isArray(propsId) ? propsId[0] : propsId
const portfolioId = rawId ?? ''

const summary = ref<PortfolioSummary | null>(null)
const timeline = ref<any[]>([])
const refreshing = ref(false)
const showDeposit = ref(false)
const showWithdraw = ref(false)
const depositAmount = ref('')
const withdrawAmount = ref('')
const withdrawWarning = ref('')
const depositInput = ref<HTMLInputElement | null>(null)
const withdrawInput = ref<HTMLInputElement | null>(null)

watch(showDeposit, (val) => {
  if (val) nextTick(() => depositInput.value?.focus())
})

watch(showWithdraw, (val) => {
  if (val) {
    withdrawWarning.value = ''
    nextTick(() => withdrawInput.value?.focus())
  }
})

async function load() {
  if (!portfolioId || portfolioId === 'undefined') {
    await router.replace('/portfolios')
    return
  }

  summary.value = await getPortfolioSummary(portfolioId)
  const tl = await getPortfolioTimeline(portfolioId)
  timeline.value = tl
}

onMounted(load)

async function handleRefresh() {
  refreshing.value = true
  try {
    if (!portfolioId || portfolioId === 'undefined') {
      return
    }
    await refreshPortfolioPrices(portfolioId)
    await load()
  } finally {
    refreshing.value = false
  }
}

async function handleDeposit() {
  try {
    if (!portfolioId || portfolioId === 'undefined') return
    await deposit(portfolioId, parseNumericInput(depositAmount.value))
    showDeposit.value = false
    depositAmount.value = ''
    await load()
  } catch (e: any) {
    console.error(e)
  }
}

async function handleWithdraw() {
  withdrawWarning.value = ''
  try {
    if (!portfolioId || portfolioId === 'undefined') return
    const result = await withdraw(portfolioId, parseNumericInput(withdrawAmount.value))
    if (result.warning) {
      withdrawWarning.value = result.warning
    } else {
      showWithdraw.value = false
      withdrawAmount.value = ''
      await load()
    }
  } catch (e: any) {
    console.error(e)
  }
}

function formatNum(val: string | number, currency?: string): string {
  return formatCurrency(val, currency)
}

function formatDate(d: string): string {
  return new Date(d).toLocaleString()
}
</script>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 50;
}
.modal-content { max-width: 400px; width: 90%; }
.alert-danger { background: rgba(239,68,68,0.15); color: var(--danger); padding: 0.75rem; border-radius: 6px; margin-bottom: 1rem; }
</style>
