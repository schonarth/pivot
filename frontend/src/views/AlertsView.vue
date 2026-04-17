<template>
  <div>
    <div class="page-header">
      <h1>Alerts</h1>
      <button
        class="btn"
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
        class="alert-danger"
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
        <select v-model="newAlert.condition_type">
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
          v-model="newAlert.threshold"
          type="text"
          inputmode="decimal"
          placeholder="0.00"
        >
      </div>
      <div class="form-group">
        <label><input
          v-model="newAlert.notify_enabled"
          type="checkbox"
        > Notify me</label>
      </div>
      <div class="form-group">
        <label><input
          v-model="newAlert.auto_trade_enabled"
          type="checkbox"
        > Auto-trade</label>
      </div>
      <div
        v-if="newAlert.auto_trade_enabled"
        class="form-group"
      >
        <label>Side</label>
        <select v-model="newAlert.auto_trade_side">
          <option value="BUY">
            BUY
          </option>
          <option value="SELL">
            SELL
          </option>
        </select>
      </div>
      <div
        v-if="newAlert.auto_trade_enabled"
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
          >
          Percentage
        </label>
      </div>
      <div
        v-if="newAlert.auto_trade_enabled && sizingType === 'quantity'"
        class="form-group"
      >
        <label>Quantity</label>
        <input
          v-model.number="newAlert.auto_trade_quantity"
          type="number"
          min="1"
        >
      </div>
      <div
        v-if="newAlert.auto_trade_enabled && sizingType === 'pct'"
        class="form-group"
      >
        <label>Percentage (0-100)</label>
        <input
          v-model="newAlert.auto_trade_pct"
          type="text"
          inputmode="decimal"
          min="1"
          max="100"
          placeholder="0.00"
        >
      </div>
      <div style="display: flex; gap: 0.5rem;">
        <button
          class="btn"
          :disabled="!newAsset || !newAlert.threshold"
          @click="handleCreate"
        >
          Create
        </button>
        <button
          class="btn btn-secondary"
          @click="showCreate = false"
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
            v-if="a.auto_trade_enabled"
            class="badge badge-info"
            style="margin-left: 0.5rem;"
          >
            Auto {{ a.auto_trade_side }}
          </span>
        </div>
        <div style="display: flex; gap: 0.25rem;">
          <button
            class="btn btn-secondary btn-sm"
            @click="handlePause(a.id)"
          >
            Pause
          </button>
          <button
            class="btn btn-danger btn-sm"
            @click="handleDelete(a.id)"
          >
            Delete
          </button>
        </div>
      </div>
    </div>

    <div
      v-if="triggeredAlerts.length"
      class="card"
    >
      <h3 style="margin-bottom: 0.75rem;">
        Triggered
      </h3>
      <div
        v-for="a in triggeredAlerts"
        :key="a.id"
        style="padding: 0.5rem 0; border-bottom: 1px solid var(--border);"
      >
        <span class="text-muted">{{ a.asset_display_symbol }}</span>
        <span style="margin-left: 0.5rem;">{{ a.condition_type }} {{ a.threshold }}</span>
        <span
          style="margin-left: 0.5rem; font-size: 0.75rem;"
          class="text-muted"
        >Triggered {{ a.triggered_at ? formatDate(a.triggered_at) : 'N/A' }}</span>
      </div>
    </div>

    <div
      v-if="!alerts.length"
      class="card"
    >
      <p class="text-muted">
        No alerts created yet.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getAlerts, createAlert, deleteAlert, pauseAlert } from '@/api/alerts'
import { searchAssets, getAsset, getAssetPrice } from '@/api/assets'
import { getPortfolio } from '@/api/portfolios'
import { parseNumericInput } from '@/utils/numbers'
import type { Alert, Asset } from '@/types'

const props = defineProps<{ id?: string | string[] }>()
const route = useRoute()
const router = useRouter()

const routePortfolioId = route.params.id as string | string[] | undefined
const propsId = props.id ?? routePortfolioId
const rawId = Array.isArray(propsId) ? propsId[0] : propsId
const portfolioId = rawId ?? ''

const alerts = ref<Alert[]>([])
const showCreate = ref(false)
const createError = ref('')
const assetSearch = ref('')
const assetResults = ref<Asset[]>([])
const newAsset = ref<Asset | null>(null)
const presetAsset = ref(false)
const selectedAssetPrice = ref<string | null>(null)
const sizingType = ref<'quantity' | 'pct'>('quantity')

const newAlert = ref({
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

onMounted(async () => {
  if (!portfolioId) {
    await router.replace('/')
    return
  }
  alerts.value = await getAlerts(portfolioId)

  const presetAssetId = route.query.asset as string | undefined
  if (presetAssetId) {
    try {
      const asset = await getAsset(presetAssetId)
      selectNewAsset(asset)
      presetAsset.value = true
      showCreate.value = true
    } catch {}
  }
})

let searchTimeout: ReturnType<typeof setTimeout>
function searchAssetsDebounced() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(async () => {
    if (assetSearch.value.length < 2) return
    try {
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

async function handleCreate() {
  createError.value = ''
  if (!newAsset.value) return
  try {
    const payload: any = {
      asset_id: newAsset.value.id,
      condition_type: newAlert.value.condition_type,
      threshold: parseNumericInput(newAlert.value.threshold),
      notify_enabled: newAlert.value.notify_enabled,
      auto_trade_enabled: newAlert.value.auto_trade_enabled,
    }
    if (newAlert.value.auto_trade_enabled) {
      payload.auto_trade_side = newAlert.value.auto_trade_side
      if (sizingType.value === 'quantity') {
        payload.auto_trade_quantity = newAlert.value.auto_trade_quantity
      } else {
        payload.auto_trade_pct = parseNumericInput(newAlert.value.auto_trade_pct ?? '0')
      }
    }
    await createAlert(portfolioId, payload)
    showCreate.value = false
    alerts.value = await getAlerts(portfolioId)
  } catch (e: any) {
    createError.value = e.response?.data?.error?.message || 'Failed to create alert'
  }
}

async function handlePause(id: string) {
  await pauseAlert(id)
  alerts.value = await getAlerts(portfolioId)
}

async function handleDelete(id: string) {
  await deleteAlert(id)
  alerts.value = await getAlerts(portfolioId)
}

function formatDate(d: string): string {
  return d ? new Date(d).toLocaleString() : '-'
}
</script>

<style scoped>
.alert-danger { background: rgba(239,68,68,0.15); color: var(--danger); padding: 0.75rem; border-radius: 6px; margin-bottom: 1rem; }
</style>
