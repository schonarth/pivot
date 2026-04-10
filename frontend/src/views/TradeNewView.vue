<template>
  <div>
    <div class="page-header">
      <h1>New Trade</h1>
      <router-link :to="`/portfolios/${portfolioId}`" class="btn btn-secondary">Back to Portfolio</router-link>
    </div>
    <div class="card" style="max-width: 600px;">
      <div v-if="error" class="alert-danger">{{ error }}</div>
      <div class="form-group">
        <label>Action</label>
        <select v-model="action">
          <option value="BUY">BUY</option>
          <option value="SELL">SELL</option>
        </select>
      </div>
      <div class="form-group">
        <label>Search Asset</label>
        <input v-model="searchQuery" type="text" placeholder="Type to search assets..." @input="doSearch" />
        <div v-if="searchResults.length" style="margin-top: 0.5rem; max-height: 200px; overflow-y: auto; border: 1px solid var(--border); border-radius: 6px;">
          <div v-for="a in searchResults" :key="a.id" style="padding: 0.5rem 0.75rem; cursor: pointer; border-bottom: 1px solid var(--border);" @click="selectAsset(a)">
            <strong>{{ a.display_symbol }}</strong> - {{ a.name }}
            <span class="badge badge-info" style="margin-left: 0.5rem;">{{ a.market }}</span>
          </div>
        </div>
      </div>
      <div v-if="selectedAsset" class="card" style="margin-bottom: 1rem;">
        <div style="display: flex; justify-content: space-between;">
          <strong>{{ selectedAsset.display_symbol }}</strong>
          <span>{{ selectedAsset.name }}</span>
        </div>
        <div v-if="currentPrice" style="margin-top: 0.5rem;">
          <span>Current Price: </span>
          <strong>{{ currentPrice.currency }} {{ Number(currentPrice.price).toFixed(4) }}</strong>
          <span v-if="currentPrice.market_open" class="badge badge-success" style="margin-left: 0.5rem;">Market Open</span>
          <span v-else class="badge badge-warning" style="margin-left: 0.5rem;">Market Closed</span>
        </div>
      </div>
      <div class="form-group">
        <label>Quantity</label>
        <input v-model.number="quantity" type="number" min="1" step="1" />
      </div>
      <div class="form-group">
        <label>Rationale (optional)</label>
        <input v-model="rationale" type="text" placeholder="Manual operation" />
      </div>
      <div v-if="preview" class="card" style="margin-bottom: 1rem;">
        <div style="display: flex; justify-content: space-between;"><span>Gross Value:</span><span>{{ preview.gross }}</span></div>
        <div style="display: flex; justify-content: space-between;"><span>Fees:</span><span>{{ preview.fees }}</span></div>
        <div style="display: flex; justify-content: space-between;"><span>Net Cash Impact:</span><span>{{ preview.net }}</span></div>
      </div>
      <button class="btn" :disabled="!selectedAsset || !quantity || loading" @click="handleSubmit">
        <span v-if="loading" class="spinner"></span>
        {{ action }} Trade
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { searchAssets as apiSearchAssets, getAssetPrice, getAsset } from '@/api/assets'
import { createTrade } from '@/api/trades'
import { getPortfolio } from '@/api/portfolios'
import type { Asset, AssetQuote } from '@/types'

const props = defineProps<{ id?: string | string[] }>()
const route = useRoute()
const router = useRouter()

const routePortfolioId = route.params.id as string | string[] | undefined
const propsId = props.id ?? routePortfolioId
const rawId = Array.isArray(propsId) ? propsId[0] : propsId
const portfolioId = rawId ?? ''

const preselectedAssetId = (route.query.asset as string) || null

const action = ref<'BUY' | 'SELL'>('BUY')
const searchQuery = ref('')
const searchResults = ref<Asset[]>([])
const selectedAsset = ref<Asset | null>(null)
const currentPrice = ref<AssetQuote | null>(null)
const quantity = ref<number | null>(null)
const rationale = ref('')
const error = ref('')
const loading = ref(false)
const feeRate = ref<number>(0)

const preview = computed(() => {
  if (!selectedAsset.value || !quantity.value || !currentPrice.value) return null
  const price = Number(currentPrice.value.price)
  const qty = quantity.value
  const gross = price * qty
  const fees = gross * feeRate.value
  const net = action.value === 'BUY' ? -(gross + fees) : gross - fees
  return {
    gross: gross.toFixed(2),
    fees: fees.toFixed(2),
    net: net.toFixed(2),
  }
})

let searchTimeout: ReturnType<typeof setTimeout>

onMounted(async () => {
  try {
    const portfolio = await getPortfolio(portfolioId)
    feeRate.value = portfolio.market === 'BR' ? 0.0003 : portfolio.market === 'US' ? 0 : 0.001
  } catch {}

  if (preselectedAssetId) {
    try {
      const asset = await getAsset(preselectedAssetId)
      await selectAsset(asset)
    } catch {}
  }
})

function doSearch() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(async () => {
    if (searchQuery.value.length < 2) {
      searchResults.value = []
      return
    }
    try {
      if (!portfolioId) return
      const portfolio = await getPortfolio(portfolioId)
      searchResults.value = await apiSearchAssets(searchQuery.value, portfolio.market)
      feeRate.value = portfolio.market === 'BR' ? 0.0003 : portfolio.market === 'US' ? 0 : 0.001
    } catch {
      searchResults.value = []
    }
  }, 300)
}

async function selectAsset(asset: Asset) {
  selectedAsset.value = asset
  searchResults.value = []
  searchQuery.value = asset.display_symbol
  try {
    currentPrice.value = await getAssetPrice(asset.id)
  } catch {
    currentPrice.value = null
  }
}

async function handleSubmit() {
  if (!portfolioId) return
  if (!selectedAsset.value || !quantity.value) return
  error.value = ''
  loading.value = true
  try {
    await createTrade(portfolioId, selectedAsset.value.id, action.value, quantity.value, rationale.value || undefined)
    router.push(`/portfolios/${portfolioId}`)
  } catch (e: any) {
    error.value = e.response?.data?.error?.message || 'Trade failed'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.alert-danger { background: rgba(239,68,68,0.15); color: var(--danger); padding: 0.75rem; border-radius: 6px; margin-bottom: 1rem; }
</style>
