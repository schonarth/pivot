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
    <div style="margin-top: 1rem; display: flex; gap: 0.5rem;">
      <router-link v-if="primaryPortfolioId" :to="`/portfolios/${primaryPortfolioId}/trades/new?asset=${asset.id}`" class="btn">Trade</router-link>
      <span v-else class="btn btn-secondary" style="pointer-events: auto; cursor: default; opacity: 0.6;" title="Create a portfolio first">Trade</span>
      <button class="btn btn-secondary" @click="showNewAlert = true">Create Alert</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getAsset, getAssetPrice, refreshAssetPrice } from '@/api/assets'
import { getPortfolios } from '@/api/portfolios'
import type { Asset, AssetQuote } from '@/types'

const route = useRoute()
const assetId = route.params.symbol as string

const asset = ref<Asset | null>(null)
const quote = ref<AssetQuote | null>(null)
const refreshing = ref(false)
const showNewAlert = ref(false)
const primaryPortfolioId = ref<string | null>(null)

async function load() {
  asset.value = await getAsset(assetId)
  try {
    quote.value = await getAssetPrice(assetId)
  } catch {
    quote.value = null
  }

  try {
    const portfolios = await getPortfolios()
    if (portfolios.length > 0) {
      const primary = portfolios.find((p) => p.is_primary) || portfolios[0]
      primaryPortfolioId.value = primary.id
    }
  } catch {}
}

onMounted(load)

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