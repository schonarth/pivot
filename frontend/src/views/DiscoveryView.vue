<template>
  <div class="discovery-view">
    <div class="page-header">
      <div>
        <h1>Opportunity Discovery</h1>
        <p class="text-muted">
          Bounded shortlist from the current market universe.
        </p>
      </div>
      <div class="discovery-actions">
        <select
          v-model="selectedMarket"
          class="market-select"
        >
          <option
            v-for="market in markets"
            :key="market"
            :value="market"
          >
            {{ market }}
          </option>
        </select>
        <button
          class="btn btn-secondary"
          :disabled="loading"
          @click="refreshDiscovery"
        >
          {{ loading ? 'Loading...' : 'Refresh' }}
        </button>
        <button
          v-if="canRefine"
          class="btn"
          :disabled="loading"
          @click="refreshRefinedDiscovery"
        >
          {{ loading ? 'Refreshing refined...' : 'Refresh refined' }}
        </button>
      </div>
    </div>

    <div class="grid grid-4 discovery-metrics">
      <div class="card">
        <div class="text-muted">Universe</div>
        <div class="metric-value">{{ result?.universe_size ?? 0 }}</div>
      </div>
      <div class="card">
        <div class="text-muted">Survivors</div>
        <div class="metric-value">{{ result?.survivor_count ?? 0 }}</div>
      </div>
      <div class="card">
        <div class="text-muted">Shortlist</div>
        <div class="metric-value">{{ result?.shortlist_count ?? 0 }}</div>
      </div>
      <div class="card">
        <div class="text-muted">Market</div>
        <div class="metric-value">{{ selectedMarket }}</div>
      </div>
    </div>

    <div
      v-if="notice"
      class="card discovery-notice"
    >
      {{ notice }}
    </div>

    <div
      v-if="!portfolioId"
      class="card"
    >
      <p class="text-muted">
        Create a portfolio first to use the watch action.
      </p>
    </div>

    <div
      v-if="loading && !result"
      class="card"
    >
      <span class="spinner" />
    </div>

    <div
      v-else-if="result"
      class="discovery-list"
    >
      <article
        v-for="item in result.shortlist"
        :key="item.asset_id"
        class="card discovery-item"
      >
        <div class="discovery-item-top">
          <div>
            <div class="discovery-rank">
              #{{ item.rank }} · {{ item.symbol }}
            </div>
            <div class="text-muted">
              {{ item.market }} · score {{ item.score }}
            </div>
          </div>
          <div class="discovery-item-actions">
            <button
              class="btn btn-secondary btn-sm"
              :disabled="watchingAssetId === item.asset_id || !portfolioId || !item.watch_action_ready"
              @click="addToWatch(item)"
            >
              {{ watchingAssetId === item.asset_id ? 'Adding...' : 'Watch' }}
            </button>
            <router-link
              class="btn btn-sm"
              :to="`/assets/${item.asset_id}`"
            >
              Open
            </router-link>
          </div>
        </div>

        <p class="discovery-reason">
          {{ item.refined_reason || item.discovery_reason }}
        </p>

        <div class="discovery-signals">
          <span class="badge badge-secondary">
            Liquidity {{ item.technical_signals.liquidity_floor_met ? 'ok' : 'low' }}
          </span>
          <span class="badge badge-secondary">
            Trend {{ item.technical_signals.trend_intact ? 'intact' : 'broken' }}
          </span>
          <span class="badge badge-secondary">
            Breakout {{ item.technical_signals.breakout_confirmed ? 'near' : 'none' }}
          </span>
          <span class="badge badge-secondary">
            Context {{ item.score_breakdown.context_support }}
          </span>
          <span
            v-if="item.refined_reason"
            class="badge badge-secondary"
          >
            Refined
          </span>
        </div>
      </article>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'
import { getSettings } from '@/api/ai'
import { addPortfolioWatchAsset, getPortfolios } from '@/api/portfolios'
import { getDiscovery, type DiscoveryResult, type DiscoveryShortlistItem } from '@/api/discovery'
import type { Portfolio } from '@/types'

const markets = ['US', 'BR', 'UK', 'EU']
const selectedMarket = ref('US')
const result = ref<DiscoveryResult | null>(null)
const loading = ref(false)
const notice = ref('')
const canRefine = ref(false)
const watchingAssetId = ref('')
const portfolios = ref<Portfolio[]>([])

const router = useRouter()
const toast = useToast()

const portfolioId = computed(() => portfolios.value.find((portfolio) => portfolio.is_primary)?.id ?? portfolios.value[0]?.id ?? null)

onMounted(async () => {
  await loadPortfolios()
  await loadAiAccess()
  await loadDiscovery()
})

watch(selectedMarket, async () => {
  await loadDiscovery()
})

async function loadPortfolios() {
  try {
    portfolios.value = await getPortfolios()
  } catch {
    portfolios.value = []
  }
}

async function loadAiAccess() {
  try {
    const settings = await getSettings()
    canRefine.value = Boolean(settings.enabled && (settings.has_api_key || settings.can_use_instance_default))
  } catch {
    canRefine.value = false
  }
}

async function loadDiscovery(options: { refine?: boolean; refresh?: boolean } = {}) {
  loading.value = true
  notice.value = ''
  try {
    result.value = await getDiscovery(selectedMarket.value, {
      refine: options.refine ?? canRefine.value,
      refresh: options.refresh ?? false,
    })
    notice.value = result.value.refinement.applied
      ? (result.value.refinement.cache_hit ? 'Refined shortlist reused from cache.' : 'Refined shortlist loaded.')
      : 'Deterministic shortlist loaded.'
  } catch (error) {
    console.error(error)
    toast.error('Failed to load discovery')
  } finally {
    loading.value = false
  }
}

async function refreshDiscovery() {
  await loadDiscovery({ refine: false, refresh: true })
}

async function refreshRefinedDiscovery() {
  await loadDiscovery({ refine: true, refresh: true })
}

async function addToWatch(item: DiscoveryShortlistItem) {
  if (!portfolioId.value || watchingAssetId.value) return
  watchingAssetId.value = item.asset_id
  try {
    await addPortfolioWatchAsset(portfolioId.value, item.asset_id)
    toast.success(`Added ${item.symbol} to watch`)
    await router.push({ path: `/portfolios/${portfolioId.value}`, query: { tab: 'watch' } })
  } catch {
    toast.error(`Failed to add ${item.symbol} to watch`)
  } finally {
    watchingAssetId.value = ''
  }
}
</script>

<style scoped>
.discovery-view {
  display: grid;
  gap: 1rem;
}

.discovery-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex-wrap: wrap;
}

.market-select {
  min-width: 5rem;
  height: 2.5rem;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--bg-primary);
  color: var(--text);
  padding: 0 0.75rem;
}

.discovery-metrics .card {
  min-height: 7rem;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.metric-value {
  font-size: 2rem;
  font-weight: 700;
}

.discovery-list {
  display: grid;
  gap: 1rem;
}

.discovery-item {
  display: grid;
  gap: 0.75rem;
}

.discovery-item-top {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
}

.discovery-item-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.discovery-rank {
  font-size: 1.1rem;
  font-weight: 700;
}

.discovery-reason {
  margin: 0;
  color: var(--text);
}

.discovery-signals {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.discovery-notice {
  color: var(--text-muted);
}
</style>
