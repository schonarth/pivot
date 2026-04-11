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

    <div class="tabs" style="margin-top: 2rem;">
      <button class="tab-btn" :class="{ active: activeTab === 'positions' }" @click="activeTab = 'positions'">Positions</button>
      <button class="tab-btn" :class="{ active: activeTab === 'alerts' }" @click="activeTab = 'alerts'">
        Alerts
        <span v-if="activeAlerts.length" class="badge badge-info" style="margin-left: 0.4rem; font-size: 0.7rem;">{{ activeAlerts.length }}</span>
      </button>
    </div>

    <div v-if="activeTab === 'positions'">
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
              <th></th>
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
              <td style="text-align: center;">
                <span v-if="assetsWithAlerts.has(pos.asset_id)" class="alert-indicator" title="Active alerts for this asset">!</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="card">
        <p class="text-muted">No positions yet. Start by making a trade!</p>
      </div>
    </div>

    <div v-if="activeTab === 'alerts'">
      <div style="display: flex; justify-content: flex-end; margin-bottom: 0.75rem;">
        <button class="btn btn-sm" @click="showCreate = true">New Alert</button>
      </div>

      <div v-if="showCreate" class="card" style="margin-bottom: 1rem;">
        <h3 style="margin-bottom: 1rem;">Create Alert</h3>
        <div v-if="createError" class="alert-error">{{ createError }}</div>
        <div class="form-group">
          <label>Asset</label>
          <template v-if="newAsset && presetAsset">
            <div>{{ newAsset.display_symbol }} — {{ newAsset.name }}</div>
          </template>
          <template v-else>
            <input v-model="assetSearch" type="text" placeholder="Search asset..." @input="searchAssetsDebounced" />
            <div v-if="assetResults.length" style="margin-top: 0.25rem; max-height: 150px; overflow-y: auto; border: 1px solid var(--border); border-radius: 6px;">
              <div v-for="a in assetResults" :key="a.id" style="padding: 0.5rem; cursor: pointer; border-bottom: 1px solid var(--border);" @click="selectNewAsset(a)">
                {{ a.display_symbol }} - {{ a.name }}
              </div>
            </div>
            <div v-if="newAsset" style="margin-top: 0.5rem;" class="text-muted">Selected: {{ newAsset.display_symbol }}</div>
          </template>
        </div>
        <div class="form-group">
          <label>Condition</label>
          <select v-model="newAlertForm.condition_type">
            <option value="price_above">Price Above</option>
            <option value="price_below">Price Below</option>
          </select>
        </div>
        <div class="form-group">
          <label>
            Threshold
            <span v-if="selectedAssetPrice" class="text-muted" style="font-size: 0.8rem; margin-left: 0.5rem;">
              Current: {{ selectedAssetPrice }}
            </span>
          </label>
          <input v-model="newAlertForm.threshold" type="text" inputmode="decimal" placeholder="0.00" />
        </div>
        <div class="form-group">
          <label><input type="checkbox" v-model="newAlertForm.notify_enabled" /> Notify me</label>
        </div>
        <div class="form-group">
          <label><input type="checkbox" v-model="newAlertForm.auto_trade_enabled" /> Auto-trade</label>
        </div>
        <div v-if="newAlertForm.auto_trade_enabled" class="form-group">
          <label>Side</label>
          <select v-model="newAlertForm.auto_trade_side">
            <option value="BUY">BUY</option>
            <option value="SELL">SELL</option>
          </select>
        </div>
        <div v-if="newAlertForm.auto_trade_enabled" class="form-group">
          <label>
            <input type="radio" name="sizing" value="quantity" v-model="sizingType" />
            Fixed Quantity
            <input type="radio" name="sizing" value="pct" v-model="sizingType" style="margin-left: 0.75rem;" />
            Percentage
          </label>
        </div>
        <div v-if="newAlertForm.auto_trade_enabled && sizingType === 'quantity'" class="form-group">
          <label>Quantity</label>
          <input v-model.number="newAlertForm.auto_trade_quantity" type="number" min="1" />
        </div>
        <div v-if="newAlertForm.auto_trade_enabled && sizingType === 'pct'" class="form-group">
          <label>Percentage (0-100)</label>
          <input v-model="newAlertForm.auto_trade_pct" type="text" inputmode="decimal" placeholder="0.00" />
        </div>
        <div style="display: flex; gap: 0.5rem;">
          <button class="btn" @click="handleCreateAlert" :disabled="!newAsset || !newAlertForm.threshold">Create</button>
          <button class="btn btn-secondary" @click="cancelCreate">Cancel</button>
        </div>
      </div>

      <div v-if="activeAlerts.length" class="card" style="margin-bottom: 1rem;">
        <h3 style="margin-bottom: 0.75rem;">Active</h3>
        <div v-for="a in activeAlerts" :key="a.id" style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 0; border-bottom: 1px solid var(--border);">
          <div>
            <strong>{{ a.asset_display_symbol }}</strong>
            <span class="badge" :class="a.condition_type === 'price_above' ? 'badge-success' : 'badge-danger'" style="margin-left: 0.5rem;">
              {{ a.condition_type === 'price_above' ? 'Above' : 'Below' }} {{ a.threshold }}
            </span>
            <span v-if="alertPrices[a.asset]" class="text-muted" style="font-size: 0.8rem; margin-left: 0.5rem;">
              now {{ alertPrices[a.asset] }}
            </span>
            <span v-if="a.auto_trade_enabled" class="badge badge-info" style="margin-left: 0.5rem;">
              Auto {{ a.auto_trade_side }}
              <template v-if="a.auto_trade_quantity"> {{ a.auto_trade_quantity }} shares</template>
              <template v-else-if="a.auto_trade_pct"> {{ a.auto_trade_pct }}%</template>
            </span>
          </div>
          <div style="display: flex; gap: 0.25rem;">
            <button class="btn btn-secondary btn-sm" @click="handlePauseAlert(a.id)">Pause</button>
            <button class="btn btn-danger btn-sm" @click="handleDeleteAlert(a.id)">Delete</button>
          </div>
        </div>
      </div>

      <div v-if="triggeredAlerts.length" class="card" style="margin-bottom: 1rem;">
        <h3 style="margin-bottom: 0.75rem;">Triggered</h3>
        <div v-for="a in triggeredAlerts" :key="a.id" style="padding: 0.75rem 0; border-bottom: 1px solid var(--border);">
          <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
              <strong>{{ a.asset_display_symbol }}</strong>
              <span class="badge" :class="a.condition_type === 'price_above' ? 'badge-success' : 'badge-danger'" style="margin-left: 0.5rem;">
                {{ a.condition_type === 'price_above' ? 'Above' : 'Below' }} {{ a.threshold }}
              </span>
              <span v-if="a.latest_trigger" style="margin-left: 0.5rem; font-size: 0.8rem;" class="text-muted">
                @ {{ a.latest_trigger.triggered_price }}
              </span>
            </div>
            <span class="text-muted" style="font-size: 0.75rem; white-space: nowrap; margin-left: 1rem;">
              {{ a.triggered_at ? formatDate(a.triggered_at) : 'N/A' }}
            </span>
          </div>
          <div v-if="a.latest_trigger" style="margin-top: 0.4rem; font-size: 0.82rem;">
            <template v-if="a.latest_trigger.trade">
              <span class="badge" :class="a.latest_trigger.trade.action === 'BUY' ? 'badge-success' : 'badge-danger'">
                {{ a.latest_trigger.trade.action }}
              </span>
              <span style="margin-left: 0.4rem;">
                {{ a.latest_trigger.trade.quantity }} shares @ {{ a.latest_trigger.trade.price }}
                (gross {{ a.latest_trigger.trade.gross_value }}<template v-if="Number(a.latest_trigger.trade.fees) > 0">, fees {{ a.latest_trigger.trade.fees }}</template>)
              </span>
            </template>
            <template v-else>
              <span class="text-muted">{{ outcomeLabel(a.latest_trigger.outcome) }}</span>
            </template>
          </div>
        </div>
      </div>

      <div v-if="pausedAlerts.length" class="card" style="margin-bottom: 1rem;">
        <h3 style="margin-bottom: 0.75rem;">Paused</h3>
        <div v-for="a in pausedAlerts" :key="a.id" style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 0; border-bottom: 1px solid var(--border);">
          <div>
            <strong>{{ a.asset_display_symbol }}</strong>
            <span class="badge badge-warning" style="margin-left: 0.5rem;">
              {{ a.condition_type === 'price_above' ? 'Above' : 'Below' }} {{ a.threshold }}
            </span>
          </div>
          <div style="display: flex; gap: 0.25rem;">
            <button class="btn btn-secondary btn-sm" @click="handleResumeAlert(a.id)">Resume</button>
            <button class="btn btn-danger btn-sm" @click="handleDeleteAlert(a.id)">Delete</button>
          </div>
        </div>
      </div>

      <div v-if="!alerts.length" class="card"><p class="text-muted">No alerts yet.</p></div>
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
        <div v-if="withdrawWarning" class="alert-error">{{ withdrawWarning }}</div>
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
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getPortfolioSummary, getPortfolioTimeline, refreshPortfolioPrices, deposit, withdraw } from '@/api/portfolios'
import { getAlerts, createAlert, deleteAlert, pauseAlert, resumeAlert } from '@/api/alerts'
import { searchAssets, getAssetPrice } from '@/api/assets'
import { parseNumericInput, formatCurrency } from '@/utils/numbers'
import type { Alert, Asset, PortfolioSummary } from '@/types'

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

const activeTab = ref<'positions' | 'alerts'>('positions')

const alerts = ref<Alert[]>([])
const alertPrices = ref<Record<string, string>>({})
const showCreate = ref(false)
const createError = ref('')
const assetSearch = ref('')
const assetResults = ref<Asset[]>([])
const newAsset = ref<Asset | null>(null)
const presetAsset = ref(false)
const selectedAssetPrice = ref<string | null>(null)
const sizingType = ref<'quantity' | 'pct'>('quantity')
const newAlertForm = ref({
  condition_type: 'price_above' as 'price_above' | 'price_below',
  threshold: '',
  notify_enabled: true,
  auto_trade_enabled: false,
  auto_trade_side: 'BUY' as 'BUY' | 'SELL',
  auto_trade_quantity: undefined as number | undefined,
  auto_trade_pct: undefined as string | undefined,
})

const activeAlerts = computed(() => alerts.value.filter((a) => a.status === 'active'))
const triggeredAlerts = computed(() => alerts.value.filter((a) => a.status === 'triggered'))
const pausedAlerts = computed(() => alerts.value.filter((a) => a.status === 'paused'))
const assetsWithAlerts = computed(() => new Set(activeAlerts.value.map((a) => a.asset)))

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
  timeline.value = await getPortfolioTimeline(portfolioId)
  await loadAlerts()
}

async function loadAlerts() {
  alerts.value = await getAlerts(portfolioId)
  const assetIds = [...new Set(activeAlerts.value.map((a) => a.asset))]
  const priceResults = await Promise.all(
    assetIds.map((id) => getAssetPrice(id).then((q) => ({ id, price: q.price })).catch(() => null))
  )
  const map: Record<string, string> = {}
  for (const result of priceResults) {
    if (result) map[result.id] = result.price
  }
  alertPrices.value = map
}

onMounted(load)

async function handleRefresh() {
  refreshing.value = true
  try {
    if (!portfolioId || portfolioId === 'undefined') return
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

let searchTimeout: ReturnType<typeof setTimeout>
function searchAssetsDebounced() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(async () => {
    if (assetSearch.value.length < 2) return
    try {
      const { getPortfolio } = await import('@/api/portfolios')
      const portfolio = await getPortfolio(portfolioId)
      assetResults.value = await searchAssets(assetSearch.value, portfolio.market)
    } catch {
      assetResults.value = []
    }
  }, 300)
}

async function selectNewAsset(asset: Asset) {
  newAsset.value = asset
  assetSearch.value = asset.display_symbol
  assetResults.value = []
  selectedAssetPrice.value = null
  try {
    const quote = await getAssetPrice(asset.id)
    selectedAssetPrice.value = quote.price
  } catch {}
}

function cancelCreate() {
  showCreate.value = false
  newAsset.value = null
  presetAsset.value = false
  assetSearch.value = ''
  assetResults.value = []
  selectedAssetPrice.value = null
  newAlertForm.value = {
    condition_type: 'price_above',
    threshold: '',
    notify_enabled: true,
    auto_trade_enabled: false,
    auto_trade_side: 'BUY',
    auto_trade_quantity: undefined,
    auto_trade_pct: undefined,
  }
}

async function handleCreateAlert() {
  createError.value = ''
  if (!newAsset.value) return
  try {
    const payload: any = {
      asset_id: newAsset.value.id,
      condition_type: newAlertForm.value.condition_type,
      threshold: parseNumericInput(newAlertForm.value.threshold),
      notify_enabled: newAlertForm.value.notify_enabled,
      auto_trade_enabled: newAlertForm.value.auto_trade_enabled,
    }
    if (newAlertForm.value.auto_trade_enabled) {
      payload.auto_trade_side = newAlertForm.value.auto_trade_side
      if (sizingType.value === 'quantity') {
        payload.auto_trade_quantity = newAlertForm.value.auto_trade_quantity
      } else {
        payload.auto_trade_pct = parseNumericInput(newAlertForm.value.auto_trade_pct ?? '0')
      }
    }
    await createAlert(portfolioId, payload)
    cancelCreate()
    await loadAlerts()
  } catch (e: any) {
    createError.value = e.response?.data?.error?.message || 'Failed to create alert'
  }
}

async function handlePauseAlert(id: string) {
  await pauseAlert(id)
  await loadAlerts()
}

async function handleResumeAlert(id: string) {
  await resumeAlert(id)
  await loadAlerts()
}

async function handleDeleteAlert(id: string) {
  await deleteAlert(id)
  await loadAlerts()
}

function formatNum(val: string | number): string {
  return formatCurrency(val)
}

function formatDate(d: string): string {
  return new Date(d).toLocaleString()
}

function outcomeLabel(outcome: string): string {
  const labels: Record<string, string> = {
    notification_only: 'Notification sent, no trade',
    trade_skipped: 'Trade skipped (insufficient funds or position)',
    trade_failed: 'Trade failed',
    notification_and_trade_skipped: 'Notification sent, trade skipped',
    notification_and_trade_failed: 'Notification sent, trade failed',
  }
  return labels[outcome] ?? outcome
}
</script>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 50;
}
.modal-content { max-width: 400px; width: 90%; }
.alert-error { background: rgba(239,68,68,0.15); color: var(--danger); padding: 0.75rem; border-radius: 6px; margin-bottom: 1rem; }

.tabs {
  display: flex;
  gap: 0;
  border-bottom: 2px solid var(--border);
  margin-bottom: 1rem;
}
.tab-btn {
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  padding: 0.5rem 1.25rem;
  font-size: 0.95rem;
  color: var(--text-secondary);
  cursor: pointer;
  font-weight: 500;
}
.tab-btn.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
}
.alert-indicator {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.25rem;
  height: 1.25rem;
  border-radius: 50%;
  background: var(--danger);
  color: #fff;
  font-size: 0.7rem;
  font-weight: 700;
  cursor: default;
}
</style>
