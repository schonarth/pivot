<template>
  <div
    v-if="loading"
    class="portfolio-loading"
  >
    <span class="spinner" />
  </div>
  <div
    v-else-if="summary"
    class="portfolio-detail"
    :class="{ 'portfolio-detail-simulating': summary.is_simulating }"
  >
    <div
      v-if="summary.is_simulating"
      class="portfolio-detail-simulating-overlay"
    />
    <div class="page-header">
      <div style="display: flex; align-items: center; gap: 0.75rem;">
        <h1>{{ summary.name }}</h1>
        <span
          v-if="summary.is_simulating"
          class="badge badge-warning"
          title="Alerts will fire on simulated prices"
        >Simulating</span>
      </div>
      <div style="display: flex; gap: 0.5rem; align-items: center;">
        <button
          class="btn btn-secondary btn-sm"
          :disabled="refreshing"
          @click="handleRefresh"
        >
          Refresh Prices
        </button>
        <button
          class="btn btn-secondary btn-sm"
          @click="showDeposit = true"
        >
          Deposit
        </button>
        <button
          class="btn btn-secondary btn-sm"
          @click="showWithdraw = true"
        >
          Withdraw
        </button>
        <router-link
          :to="`/portfolios/${portfolioId}/trades/new`"
          class="btn btn-sm"
        >
          New Trade
        </router-link>
        <label class="toggle-switch">
          <input
            type="checkbox"
            :checked="summary.is_simulating"
            @change="handleToggleSimulating"
          >
          <span class="toggle-label">{{ summary.is_simulating ? 'Simulating' : 'Real' }}</span>
        </label>
      </div>
    </div>
    <div class="grid grid-4">
      <div class="card">
        <div
          class="text-muted"
          style="font-size: 0.75rem;"
        >
          Total Equity
        </div>
        <div style="font-size: 1.25rem; font-weight: 600;">
          {{ summary.base_currency }} {{ formatNum(summary.total_equity) }}
        </div>
      </div>
      <div class="card">
        <div
          class="text-muted"
          style="font-size: 0.75rem;"
        >
          Cash
        </div>
        <div style="font-size: 1.25rem; font-weight: 600;">
          {{ summary.base_currency }} {{ formatNum(summary.current_cash) }}
        </div>
      </div>
      <div class="card">
        <div
          class="text-muted"
          style="font-size: 0.75rem;"
        >
          Invested
        </div>
        <div style="font-size: 1.25rem; font-weight: 600;">
          {{ summary.base_currency }} {{ formatNum(summary.positions_value) }}
        </div>
      </div>
      <div class="card">
        <div
          class="text-muted"
          style="font-size: 0.75rem;"
        >
          Trading P&L
        </div>
        <div
          :class="Number(summary.trading_pnl) >= 0 ? 'text-success' : 'text-danger'"
          style="font-size: 1.25rem; font-weight: 600;"
        >
          {{ summary.base_currency }} {{ formatNum(summary.trading_pnl) }}
        </div>
      </div>
    </div>
    <div
      class="grid grid-2"
      style="margin-top: 1rem;"
    >
      <div class="card">
        <div
          class="text-muted"
          style="font-size: 0.75rem;"
        >
          Net Deposits/Withdrawals
        </div>
        <div style="font-size: 1rem;">
          {{ summary.base_currency }} {{ formatNum(summary.net_external_cash_flows) }}
        </div>
      </div>
      <div class="card">
        <div
          class="text-muted"
          style="font-size: 0.75rem;"
        >
          Market
        </div>
        <MarketBadge :market="summary.market" />
      </div>
    </div>

    <div
      class="tabs"
      style="margin-top: 2rem;"
    >
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'positions' }"
        @click="activeTab = 'positions'"
      >
        Positions
      </button>
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'watch' }"
        @click="activeTab = 'watch'"
      >
        Watches
        <span
          v-if="watchAssessments.length"
          class="badge badge-info"
          style="margin-left: 0.4rem; font-size: 0.7rem;"
        >{{ watchAssessments.length }}</span>
      </button>
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'alerts' }"
        @click="activeTab = 'alerts'"
      >
        Alerts
        <span
          v-if="activeAlerts.length"
          class="badge badge-info"
          style="margin-left: 0.4rem; font-size: 0.7rem;"
        >{{ activeAlerts.length }}</span>
      </button>
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'strategies' }"
        @click="activeTab = 'strategies'"
      >
        Strategies
      </button>
    </div>

    <div v-if="activeTab === 'positions'">
      <ScopeInsightCard
        title="Portfolio AI Summary"
        scope-label="Portfolio positions"
        :asset-count="positionAssessments.length"
        empty-message="No positions to analyze yet."
        :insight="portfolioInsight"
      />
      <div
        v-if="summary.positions.length"
        class="card"
      >
        <table>
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Qty</th>
              <th>Avg Cost</th>
              <th>Current Price</th>
              <th>Market Value</th>
              <th>Unrealized P&L</th>
              <th />
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="pos in summary.positions"
              :key="pos.asset_id"
            >
              <td>
                <router-link :to="`/assets/${pos.asset_id}`">
                  {{ pos.symbol }}
                </router-link>
              </td>
              <td>{{ pos.quantity }}</td>
              <td>{{ formatNum(pos.average_cost) }}</td>
              <td>{{ formatNum(pos.current_price) }}</td>
              <td>{{ formatNum(pos.market_value) }}</td>
              <td :class="Number(pos.unrealized_pnl) >= 0 ? 'text-success' : 'text-danger'">
                {{ formatNum(pos.unrealized_pnl) }}
              </td>
              <td style="text-align: center;">
                <span
                  v-if="assetsWithAlerts.has(pos.asset_id)"
                  class="alert-indicator"
                  title="Active alerts for this asset"
                >!</span>
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
          No positions yet. Start by making a trade!
        </p>
      </div>
      <div style="margin-top: 1rem;">
        <MonitoredSetAssessment
          title="Position Assessments"
          scope-label="Portfolio positions"
          empty-message="No positions to assess yet."
          :assets="positionAssessments"
        />
      </div>
    </div>

    <div v-if="activeTab === 'watch'">
      <ScopeInsightCard
        title="Watch AI Summary"
        scope-label="Portfolio watch"
        :asset-count="watchAssessments.length"
        empty-message="No watch assets to analyze yet."
        :insight="watchInsight"
      />
      <div class="card" style="margin-bottom: 1rem;">
        <h3 style="margin-bottom: 0.75rem;">
          Add to Watch
        </h3>
        <div v-if="watchCreateError" class="alert-error">
          {{ watchCreateError }}
        </div>
        <div class="form-group">
          <label>Asset</label>
          <template v-if="watchAssetSelected">
            <div>{{ watchAssetSelected.display_symbol }} — {{ watchAssetSelected.name }}</div>
          </template>
          <template v-else>
            <input
              v-model="watchAssetSearch"
              type="text"
              placeholder="Search asset..."
              @input="searchWatchAssetsDebounced"
            >
            <div
              v-if="watchAssetResults.length"
              style="margin-top: 0.25rem; max-height: 150px; overflow-y: auto; border: 1px solid var(--border); border-radius: 6px;"
            >
              <div
                v-for="a in watchAssetResults"
                :key="a.id"
                style="padding: 0.5rem; cursor: pointer; border-bottom: 1px solid var(--border);"
                @click="selectWatchAsset(a)"
              >
                {{ a.display_symbol }} - {{ a.name }}
              </div>
            </div>
          </template>
        </div>
        <div style="display: flex; gap: 0.5rem;">
          <button
            class="btn"
            :disabled="!watchAssetSelected || watchSaving"
            @click="handleAddWatchAsset"
          >
            {{ watchSaving ? 'Adding...' : 'Add to Watch' }}
          </button>
          <button
            class="btn btn-secondary"
            :disabled="watchSaving && !!watchAssetSelected"
            @click="cancelWatchCreate"
          >
            Clear
          </button>
        </div>
      </div>
      <MonitoredSetAssessment
        title="Watch Assessments"
        scope-label="Portfolio watch"
        empty-message="No watch assets yet."
        :assets="watchAssessments"
        :allow-removal="true"
        @remove="handleRemoveWatchAsset"
      />
    </div>

    <div v-if="activeTab === 'alerts'">
      <div style="display: flex; justify-content: flex-end; margin-bottom: 0.75rem;">
        <button
          class="btn btn-sm"
          @click="showCreate = true"
        >
          New Alert
        </button>
      </div>

      <div
        v-if="showCreate"
        class="card"
        style="margin-bottom: 1rem;"
      >
        <h3 style="margin-bottom: 1rem;">
          Create Alert
        </h3>
        <div
          v-if="createError"
          class="alert-error"
        >
          {{ createError }}
        </div>
        <div class="form-group">
          <label>Asset</label>
          <template v-if="newAsset && presetAsset">
            <div>{{ newAsset.display_symbol }} — {{ newAsset.name }}</div>
          </template>
          <template v-else>
            <input
              v-model="assetSearch"
              type="text"
              placeholder="Search asset..."
              @input="searchAssetsDebounced"
            >
            <div
              v-if="assetResults.length"
              style="margin-top: 0.25rem; max-height: 150px; overflow-y: auto; border: 1px solid var(--border); border-radius: 6px;"
            >
              <div
                v-for="a in assetResults"
                :key="a.id"
                style="padding: 0.5rem; cursor: pointer; border-bottom: 1px solid var(--border);"
                @click="selectNewAsset(a)"
              >
                {{ a.display_symbol }} - {{ a.name }}
              </div>
            </div>
            <div
              v-if="newAsset"
              style="margin-top: 0.5rem;"
              class="text-muted"
            >
              Selected: {{ newAsset.display_symbol }}
            </div>
          </template>
        </div>
        <div class="form-group">
          <label>Condition</label>
          <select v-model="newAlertForm.condition_type">
            <option value="price_above">
              Price Above
            </option>
            <option value="price_below">
              Price Below
            </option>
          </select>
        </div>
        <div class="form-group">
          <label>
            Threshold
            <span
              v-if="selectedAssetPrice"
              class="text-muted"
              style="font-size: 0.8rem; margin-left: 0.5rem;"
            >
              Current: {{ selectedAssetPrice }}
            </span>
          </label>
          <input
            v-model="newAlertForm.threshold"
            type="text"
            inputmode="decimal"
            placeholder="0.00"
          >
        </div>
        <div class="form-group">
          <label><input
            v-model="newAlertForm.notify_enabled"
            type="checkbox"
          > Notify me</label>
        </div>
        <div class="form-group">
          <label><input
            v-model="newAlertForm.auto_trade_enabled"
            type="checkbox"
          > Auto-trade</label>
        </div>
        <div
          v-if="newAlertForm.auto_trade_enabled"
          class="form-group"
        >
          <label>Side</label>
          <select v-model="newAlertForm.auto_trade_side">
            <option value="BUY">
              BUY
            </option>
            <option value="SELL">
              SELL
            </option>
          </select>
        </div>
        <div
          v-if="newAlertForm.auto_trade_enabled"
          class="form-group"
        >
          <label>
            <input
              v-model="sizingType"
              type="radio"
              name="sizing"
              value="quantity"
            >
            Fixed Quantity
            <input
              v-model="sizingType"
              type="radio"
              name="sizing"
              value="pct"
              style="margin-left: 0.75rem;"
            >
            Percentage
          </label>
        </div>
        <div
          v-if="newAlertForm.auto_trade_enabled && sizingType === 'quantity'"
          class="form-group"
        >
          <label>Quantity</label>
          <input
            v-model.number="newAlertForm.auto_trade_quantity"
            type="number"
            min="1"
          >
        </div>
        <div
          v-if="newAlertForm.auto_trade_enabled && sizingType === 'pct'"
          class="form-group"
        >
          <label>Percentage (0-100)</label>
          <input
            v-model="newAlertForm.auto_trade_pct"
            type="text"
            inputmode="decimal"
            placeholder="0.00"
          >
        </div>
        <div style="display: flex; gap: 0.5rem;">
          <button
            class="btn"
            :disabled="!newAsset || !newAlertForm.threshold"
            @click="handleCreateAlert"
          >
            Create
          </button>
          <button
            class="btn btn-secondary"
            @click="cancelCreate"
          >
            Cancel
          </button>
        </div>
      </div>

      <div
        v-if="activeAlerts.length"
        class="card"
        style="margin-bottom: 1rem;"
      >
        <h3 style="margin-bottom: 0.75rem;">
          Active
        </h3>
        <div
          v-for="a in activeAlerts"
          :key="a.id"
          style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 0; border-bottom: 1px solid var(--border);"
        >
          <div>
            <strong>{{ a.asset_display_symbol }}</strong>
            <span
              class="badge"
              :class="a.condition_type === 'price_above' ? 'badge-success' : 'badge-danger'"
              style="margin-left: 0.5rem;"
            >
              {{ a.condition_type === 'price_above' ? 'Above' : 'Below' }} {{ a.threshold }}
            </span>
            <span
              v-if="alertPrices[a.asset]"
              class="text-muted"
              style="font-size: 0.8rem; margin-left: 0.5rem;"
            >
              now {{ alertPrices[a.asset] }}
            </span>
            <span
              v-if="a.auto_trade_enabled"
              class="badge badge-info"
              style="margin-left: 0.5rem;"
            >
              Auto {{ a.auto_trade_side }}
              <template v-if="a.auto_trade_quantity"> {{ a.auto_trade_quantity }} shares</template>
              <template v-else-if="a.auto_trade_pct"> {{ a.auto_trade_pct }}%</template>
            </span>
          </div>
          <div style="display: flex; gap: 0.25rem;">
            <button
              class="btn btn-secondary btn-sm"
              @click="handlePauseAlert(a.id)"
            >
              Pause
            </button>
            <button
              class="btn btn-danger btn-sm"
              @click="handleDeleteAlert(a.id)"
            >
              Delete
            </button>
          </div>
        </div>
      </div>

      <div
        v-if="triggeredAlerts.length"
        class="card"
        style="margin-bottom: 1rem;"
      >
        <h3 style="margin-bottom: 0.75rem;">
          Triggered
        </h3>
        <div
          v-for="a in triggeredAlerts"
          :key="a.id"
          style="padding: 0.75rem 0; border-bottom: 1px solid var(--border);"
        >
          <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
              <strong>{{ a.asset_display_symbol }}</strong>
              <span
                class="badge"
                :class="a.condition_type === 'price_above' ? 'badge-success' : 'badge-danger'"
                style="margin-left: 0.5rem;"
              >
                {{ a.condition_type === 'price_above' ? 'Above' : 'Below' }} {{ a.threshold }}
              </span>
              <span
                v-if="a.latest_trigger"
                style="margin-left: 0.5rem; font-size: 0.8rem;"
                class="text-muted"
              >
                @ {{ a.latest_trigger.triggered_price }}
              </span>
            </div>
            <span
              class="text-muted"
              style="font-size: 0.75rem; white-space: nowrap; margin-left: 1rem;"
            >
              {{ a.triggered_at ? formatDate(a.triggered_at) : 'N/A' }}
            </span>
          </div>
          <div
            v-if="a.latest_trigger"
            style="margin-top: 0.4rem; font-size: 0.82rem;"
          >
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.3rem;">
              <template v-if="a.latest_trigger.trade">
                <span
                  class="badge"
                  :class="a.latest_trigger.trade.action === 'BUY' ? 'badge-success' : 'badge-danger'"
                >
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
            <div
              v-if="a.latest_trigger.price_was_override"
              style="font-size: 0.75rem; color: #ff9800;"
            >
              Triggered by simulated price
            </div>
          </div>
        </div>
      </div>

      <div
        v-if="pausedAlerts.length"
        class="card"
        style="margin-bottom: 1rem;"
      >
        <h3 style="margin-bottom: 0.75rem;">
          Paused
        </h3>
        <div
          v-for="a in pausedAlerts"
          :key="a.id"
          style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 0; border-bottom: 1px solid var(--border);"
        >
          <div>
            <strong>{{ a.asset_display_symbol }}</strong>
            <span
              class="badge badge-warning"
              style="margin-left: 0.5rem;"
            >
              {{ a.condition_type === 'price_above' ? 'Above' : 'Below' }} {{ a.threshold }}
            </span>
          </div>
          <div style="display: flex; gap: 0.25rem;">
            <button
              class="btn btn-secondary btn-sm"
              @click="handleResumeAlert(a.id)"
            >
              Resume
            </button>
            <button
              class="btn btn-danger btn-sm"
              @click="handleDeleteAlert(a.id)"
            >
              Delete
            </button>
          </div>
        </div>
      </div>

      <div
        v-if="!alerts.length"
        class="card"
      >
        <p class="text-muted">
          No alerts yet.
        </p>
      </div>
    </div>

    <div v-if="activeTab === 'strategies'">
      <StrategiesView :id="portfolioId" />
    </div>

    <h2 style="margin-top: 2rem; margin-bottom: 1rem;">
      Recent Activity
    </h2>
    <div
      v-if="timeline.length"
      class="card"
    >
      <div
        v-for="event in timeline.slice(0, 10)"
        :key="event.id"
        style="padding: 0.5rem 0; border-bottom: 1px solid var(--border);"
      >
        <div style="display: flex; justify-content: space-between;">
          <span>{{ event.description }}</span>
          <span
            class="text-muted"
            style="font-size: 0.75rem;"
          >{{ formatDate(event.created_at) }}</span>
        </div>
      </div>
    </div>
    <div
      v-else
      class="card"
    >
      <p class="text-muted">
        No activity yet.
      </p>
    </div>

    <div
      v-if="showDeposit"
      class="modal-overlay"
      @click.self="showDeposit = false"
    >
      <div class="card modal-content">
        <h3>Deposit</h3>
        <div class="form-group">
          <label>Amount</label>
          <input
            ref="depositInput"
            v-model="depositAmount"
            type="text"
            inputmode="decimal"
            placeholder="0.00"
            @keyup.enter="handleDeposit"
          >
        </div>
        <div style="display: flex; gap: 0.5rem; justify-content: flex-end;">
          <button
            class="btn btn-secondary"
            @click="showDeposit = false"
          >
            Cancel
          </button>
          <button
            class="btn btn-success"
            @click="handleDeposit"
          >
            Deposit
          </button>
        </div>
      </div>
    </div>

    <div
      v-if="showWithdraw"
      class="modal-overlay"
      @click.self="showWithdraw = false"
    >
      <div class="card modal-content">
        <h3>Withdraw</h3>
        <div
          v-if="withdrawWarning"
          class="alert-error"
        >
          {{ withdrawWarning }}
        </div>
        <div class="form-group">
          <label>Amount</label>
          <input
            ref="withdrawInput"
            v-model="withdrawAmount"
            type="text"
            inputmode="decimal"
            placeholder="0.00"
            @keyup.enter="handleWithdraw"
          >
        </div>
        <div style="display: flex; gap: 0.5rem; justify-content: flex-end;">
          <button
            class="btn btn-secondary"
            @click="showWithdraw = false"
          >
            Cancel
          </button>
          <button
            class="btn btn-danger"
            @click="handleWithdraw"
          >
            Withdraw
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import MarketBadge from '@/components/MarketBadge.vue'
import MonitoredSetAssessment from '@/components/MonitoredSetAssessment.vue'
import StrategiesView from '@/views/StrategiesView.vue'
import { useRoute, useRouter } from 'vue-router'
import {
  addPortfolioWatchAsset,
  getPortfolioSummary,
  getPortfolioTimeline,
  refreshPortfolioPrices,
  deposit,
  removePortfolioWatchAsset,
  withdraw,
  updatePortfolio,
} from '@/api/portfolios'
import { getAlerts, createAlert, deleteAlert, pauseAlert, resumeAlert } from '@/api/alerts'
import { searchAssets, getAssetPrice } from '@/api/assets'
import { parseNumericInput, formatCurrency } from '@/utils/numbers'
import { useWebSocketStore } from '@/stores/websocket'
import { useNotifications } from '@/composables/useNotifications'
import { useToast } from '@/composables/useToast'
import ScopeInsightCard from '@/components/ScopeInsightCard.vue'
import type { Alert, Asset, PortfolioSummary, MonitoredAssetSummary } from '@/types'

const props = defineProps<{ id?: string | string[] }>()
const route = useRoute()
const router = useRouter()
const ws = useWebSocketStore()
const { showNotification } = useNotifications()
const toast = useToast()

const getPortfolioId = () => {
  const routePortfolioId = route.params.id as string | string[] | undefined
  const propsId = props.id ?? routePortfolioId
  const rawId = Array.isArray(propsId) ? propsId[0] : propsId
  return rawId ?? ''
}

const portfolioId = ref(getPortfolioId())

const summary = ref<PortfolioSummary | null>(null)
const loading = ref(true)
const timeline = ref<any[]>([])
const refreshing = ref(false)
const showDeposit = ref(false)
const showWithdraw = ref(false)
const depositAmount = ref('')
const withdrawAmount = ref('')
const withdrawWarning = ref('')
const depositInput = ref<HTMLInputElement | null>(null)
const withdrawInput = ref<HTMLInputElement | null>(null)

const activeTab = ref<'positions' | 'watch' | 'alerts' | 'strategies'>(
  route.query.tab === 'watch' ? 'watch' : 'positions',
)

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
const watchAssetSearch = ref('')
const watchAssetResults = ref<Asset[]>([])
const watchAssetSelected = ref<Asset | null>(null)
const watchSaving = ref(false)
const watchCreateError = ref('')

const activeAlerts = computed(() => alerts.value.filter((a) => a.status === 'active'))
const triggeredAlerts = computed(() => alerts.value.filter((a) => a.status === 'triggered'))
const pausedAlerts = computed(() => alerts.value.filter((a) => a.status === 'paused'))
const assetsWithAlerts = computed(() => new Set(activeAlerts.value.map((a) => a.asset)))
const positionAssessments = computed<MonitoredAssetSummary[]>(() => {
  if (!summary.value) return []
  return summary.value.positions.map((position) => ({
    asset_id: position.asset_id,
    symbol: position.symbol,
    name: position.name,
    market: summary.value!.market,
    currency: position.currency,
    current_price: position.current_price,
  }))
})
const watchAssessments = computed<MonitoredAssetSummary[]>(() => summary.value?.watch_assets ?? [])
const portfolioInsight = computed(() => summary.value?.scope_insights?.portfolio ?? null)
const watchInsight = computed(() => summary.value?.scope_insights?.watch ?? null)

watch(showDeposit, (val) => {
  if (val) nextTick(() => depositInput.value?.focus())
})

watch(showWithdraw, (val) => {
  if (val) {
    withdrawWarning.value = ''
    nextTick(() => withdrawInput.value?.focus())
  }
})

watch(() => route.params.id, () => {
  const newPortfolioId = getPortfolioId()
  if (newPortfolioId && newPortfolioId !== portfolioId.value) {
    portfolioId.value = newPortfolioId
    load()
  }
})

watch(
  () => route.query.tab,
  (tab) => {
    if (tab === 'watch') {
      activeTab.value = 'watch'
    }
  },
  { immediate: true },
)

async function load() {
  if (!portfolioId.value || portfolioId.value === 'undefined') {
    await router.replace('/portfolios')
    return
  }
  loading.value = true
  try {
    summary.value = await getPortfolioSummary(portfolioId.value)
    timeline.value = await getPortfolioTimeline(portfolioId.value)
    await loadAlerts()
  } finally {
    loading.value = false
  }
}

async function loadAlerts() {
  alerts.value = await getAlerts(portfolioId.value)
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

onMounted(() => {
  load()
  ws.on('trade.executed', () => {
    load()
    toast.success('Trade executed')
  })
  ws.on('alert.triggered', () => {
    load()
    showNotification('Alert Triggered', {
      body: `Price alert has been triggered for your portfolio`,
      icon: '/icon.png',
    })
    toast.warning('Price alert triggered')
  })
  ws.on('price.updated', () => {
    load()
  })
  ws.on('portfolio.updated', () => {
    load()
    toast.info('Portfolio updated')
  })
})

onUnmounted(() => {
  ws.off('trade.executed')
  ws.off('alert.triggered')
  ws.off('price.updated')
  ws.off('portfolio.updated')
})

async function handleRefresh() {
  refreshing.value = true
  try {
    if (!portfolioId.value || portfolioId.value === 'undefined') return
    await refreshPortfolioPrices(portfolioId.value)
  } finally {
    refreshing.value = false
  }
}

async function handleDeposit() {
  try {
    if (!portfolioId.value || portfolioId.value === 'undefined') return
    await deposit(portfolioId.value, parseNumericInput(depositAmount.value))
    showDeposit.value = false
    depositAmount.value = ''
    await load()
    toast.success('Deposit successful')
  } catch (e: any) {
    console.error(e)
    toast.error('Failed to deposit')
  }
}

async function handleWithdraw() {
  withdrawWarning.value = ''
  try {
    if (!portfolioId.value || portfolioId.value === 'undefined') return
    const result = await withdraw(portfolioId.value, parseNumericInput(withdrawAmount.value))
    if (result.warning) {
      withdrawWarning.value = result.warning
      toast.warning(result.warning)
    } else {
      showWithdraw.value = false
      withdrawAmount.value = ''
      await load()
      toast.success('Withdrawal successful')
    }
  } catch (e: any) {
    console.error(e)
    toast.error('Failed to withdraw')
  }
}

async function handleToggleSimulating() {
  try {
    if (!portfolioId.value || portfolioId.value === 'undefined') return
    await updatePortfolio(portfolioId.value, { is_simulating: !summary.value?.is_simulating })
    await load()
    const action = summary.value?.is_simulating ? 'enabled' : 'disabled'
    toast.info(`Simulating ${action}`)
  } catch (e: any) {
    console.error(e)
    toast.error('Failed to update portfolio')
  }
}

let searchTimeout: ReturnType<typeof setTimeout>
function searchAssetsDebounced() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(async () => {
    if (assetSearch.value.length < 2) return
    try {
      const { getPortfolio } = await import('@/api/portfolios')
      const portfolio = await getPortfolio(portfolioId.value)
      assetResults.value = await searchAssets(assetSearch.value, portfolio.market)
    } catch {
      assetResults.value = []
    }
  }, 300)
}

let watchSearchTimeout: ReturnType<typeof setTimeout>
function searchWatchAssetsDebounced() {
  clearTimeout(watchSearchTimeout)
  watchSearchTimeout = setTimeout(async () => {
    if (watchAssetSearch.value.length < 2 || !summary.value) return
    try {
      watchAssetResults.value = await searchAssets(watchAssetSearch.value, summary.value.market)
    } catch {
      watchAssetResults.value = []
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

async function selectWatchAsset(asset: Asset) {
  watchAssetSelected.value = asset
  watchAssetSearch.value = asset.display_symbol
  watchAssetResults.value = []
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

function cancelWatchCreate() {
  watchCreateError.value = ''
  watchAssetSelected.value = null
  watchAssetSearch.value = ''
  watchAssetResults.value = []
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
    await createAlert(portfolioId.value, payload)
    cancelCreate()
    await loadAlerts()
    toast.success('Alert created')
  } catch (e: any) {
    createError.value = e.response?.data?.error?.message || 'Failed to create alert'
    toast.error('Failed to create alert')
  }
}

async function handleAddWatchAsset() {
  watchCreateError.value = ''
  if (!summary.value || !watchAssetSelected.value || watchSaving.value) return
  watchSaving.value = true
  try {
    await addPortfolioWatchAsset(summary.value.portfolio_id, watchAssetSelected.value.id)
    cancelWatchCreate()
    await load()
    toast.success('Watch asset added')
  } catch (e: any) {
    watchCreateError.value = e.response?.data?.error?.message || 'Failed to add watch asset'
    toast.error('Failed to add watch asset')
  } finally {
    watchSaving.value = false
  }
}

async function handleRemoveWatchAsset(assetId: string) {
  if (!summary.value) return
  try {
    await removePortfolioWatchAsset(summary.value.portfolio_id, assetId)
    await load()
    toast.success('Watch asset removed')
  } catch {
    toast.error('Failed to remove watch asset')
  }
}

async function handlePauseAlert(id: string) {
  try {
    await pauseAlert(id)
    await loadAlerts()
    toast.success('Alert paused')
  } catch {
    toast.error('Failed to pause alert')
  }
}

async function handleResumeAlert(id: string) {
  try {
    await resumeAlert(id)
    await loadAlerts()
    toast.success('Alert resumed')
  } catch {
    toast.error('Failed to resume alert')
  }
}

async function handleDeleteAlert(id: string) {
  try {
    await deleteAlert(id)
    await loadAlerts()
    toast.success('Alert deleted')
  } catch {
    toast.error('Failed to delete alert')
  }
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
.portfolio-loading {
  min-height: calc(100vh - 3.5rem);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: calc((100vh - 3.5rem) / 3);
}

.portfolio-detail {
  min-height: calc(100vh - 3.5rem);
}

.portfolio-detail-simulating {
  position: relative;
}

.portfolio-detail-simulating > * {
  position: relative;
  z-index: 1;
}

.portfolio-detail-simulating-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 193, 7, 0.03);
  pointer-events: none;
  z-index: 0;
}
</style>

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

.toggle-switch {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.toggle-switch input {
  appearance: none;
  width: 2.25rem;
  height: 1.25rem;
  border-radius: 0.625rem;
  background: var(--border);
  cursor: pointer;
  transition: background-color 0.3s;
  border: none;
  padding: 0;
  position: relative;
}

.toggle-switch input::before {
  content: '';
  position: absolute;
  width: 1rem;
  height: 1rem;
  border-radius: 50%;
  background: white;
  left: 0.125rem;
  top: 0.125rem;
  transition: left 0.3s;
}

.toggle-switch input:checked {
  background: #ffc107;
}

.toggle-switch input:checked::before {
  left: 1.125rem;
}

.toggle-switch input:focus {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.toggle-label {
  font-size: 0.875rem;
  white-space: nowrap;
  color: var(--text-secondary);
  font-weight: 500;
}
</style>
