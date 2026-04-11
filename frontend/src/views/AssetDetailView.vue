<template>
  <div v-if="asset">
    <div class="page-header">
      <h1>{{ asset.display_symbol }}</h1>
      <router-link to="/assets" class="btn btn-secondary">Back to Assets</router-link>
    </div>
    <div class="card">
      <div class="grid grid-3">
        <div><span class="text-muted">Name:</span> {{ asset.name }}</div>
        <div><span class="text-muted">Market:</span> <span class="badge badge-info">{{ asset.market }}</span></div>
        <div><span class="text-muted">Currency:</span> {{ asset.currency }}</div>
        <div><span class="text-muted">Exchange:</span> {{ asset.exchange }}</div>
        <div><span class="text-muted">Sector:</span> {{ asset.sector || '-' }}</div>
        <div><span class="text-muted">Industry:</span> {{ asset.industry || '-' }}</div>
      </div>
    </div>
    <div class="card" v-if="quote">
      <h2 style="margin-bottom: 0.75rem;">Current Price</h2>
      <div class="grid grid-3">
        <div>
          <div class="text-muted" style="font-size: 0.75rem;">Price</div>
          <div style="font-size: 1.5rem; font-weight: 600;">{{ quote.currency }} {{ Number(quote.price).toFixed(4) }}</div>
        </div>
        <div>
          <div class="text-muted" style="font-size: 0.75rem;">Quote Time</div>
          <div>{{ formatDate(quote.as_of) }}</div>
        </div>
        <div>
          <div class="text-muted" style="font-size: 0.75rem;">Status</div>
          <span v-if="quote.market_open" class="badge badge-success">Market Open</span>
          <span v-else class="badge badge-warning">Market Closed</span>
          <span v-if="quote.stale" class="badge badge-danger" style="margin-left: 0.5rem;">Stale</span>
        </div>
      </div>
      <div style="margin-top: 1rem;">
        <button class="btn btn-secondary btn-sm" @click="handleRefresh" :disabled="refreshing">
          {{ refreshing ? 'Refreshing...' : 'Refresh Price' }}
        </button>
      </div>
    </div>
    <div v-else class="card">
      <p class="text-muted">No price data available.</p>
      <button class="btn btn-secondary btn-sm" @click="handleRefresh" :disabled="refreshing">{{ refreshing ? 'Fetching...' : 'Fetch Price' }}</button>
    </div>
    <div style="margin-top: 1rem; display: flex; gap: 0.5rem; align-items: center;">
      <template v-if="matchingPortfolios.length === 1">
        <router-link :to="`/portfolios/${matchingPortfolios[0].id}/trades/new?asset=${asset.id}`" class="btn">Trade</router-link>
      </template>
      <template v-else-if="matchingPortfolios.length > 1">
        <select class="btn" style="cursor: pointer;" @change="navigateToTrade">
          <option value="">Trade in…</option>
          <option v-for="p in matchingPortfolios" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
      </template>
      <template v-else>
        <span
          class="btn"
          style="pointer-events: auto; cursor: default; opacity: 0.6;"
          :title="asset ? `No ${asset.market} portfolio` : 'Create a portfolio first'"
        >Trade</span>
      </template>

      <template v-if="matchingPortfolios.length === 1">
        <router-link :to="`/portfolios/${matchingPortfolios[0].id}/alerts?asset=${asset.id}`" class="btn btn-secondary">Create Alert</router-link>
      </template>
      <template v-else-if="matchingPortfolios.length > 1">
        <select class="btn btn-secondary" style="cursor: pointer;" @change="navigateToAlerts">
          <option value="">Create Alert in…</option>
          <option v-for="p in matchingPortfolios" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
      </template>
      <template v-else>
        <span
          class="btn btn-secondary"
          style="pointer-events: auto; cursor: default; opacity: 0.6;"
          :title="asset ? `No ${asset.market} portfolio` : 'Create a portfolio first'"
        >Create Alert</span>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getAsset, getAssetPrice, refreshAssetPrice } from '@/api/assets'
import { getPortfolios } from '@/api/portfolios'
import type { Asset, AssetQuote, Portfolio } from '@/types'

const route = useRoute()
const router = useRouter()
const assetId = route.params.symbol as string

const asset = ref<Asset | null>(null)
const quote = ref<AssetQuote | null>(null)
const refreshing = ref(false)
const primaryPortfolioId = ref<string | null>(null)
const portfolios = ref<Portfolio[]>([])

const matchingPortfolios = computed(() =>
  asset.value ? portfolios.value.filter((p) => p.market === asset.value!.market) : []
)

async function load() {
  asset.value = await getAsset(assetId)
  try {
    quote.value = await getAssetPrice(assetId)
  } catch {
    quote.value = null
  }

  try {
    portfolios.value = await getPortfolios()
    if (portfolios.value.length > 0) {
      const primary = portfolios.value.find((p) => p.is_primary) ?? portfolios.value[0]
      primaryPortfolioId.value = primary.id
    }
  } catch {}
}

onMounted(load)

function navigateToTrade(event: Event) {
  const portfolioId = (event.target as HTMLSelectElement).value
  if (!portfolioId) return
  router.push(`/portfolios/${portfolioId}/trades/new?asset=${asset.value!.id}`)
}

function navigateToAlerts(event: Event) {
  const portfolioId = (event.target as HTMLSelectElement).value
  if (!portfolioId) return
  router.push(`/portfolios/${portfolioId}/alerts?asset=${asset.value!.id}`)
}

async function handleRefresh() {
  refreshing.value = true
  try {
    quote.value = await refreshAssetPrice(assetId)
  } catch {
    try {
      quote.value = await getAssetPrice(assetId)
    } catch {
      quote.value = null
    }
  } finally {
    refreshing.value = false
  }
}

function formatDate(d: string): string {
  return new Date(d).toLocaleString()
}
</script>
