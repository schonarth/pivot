<template>
  <div class="market-status-section">
    <h2 style="margin-bottom: 0.25rem;">
      Market Status
    </h2>
    <div class="text-muted" style="font-size: 0.75rem; margin-bottom: 1rem;">
      Live market open/closed status
    </div>

    <div v-if="loading">
      <div class="grid grid-4 market-status-grid">
        <div
          v-for="market in markets"
          :key="market"
          class="card market-status-skeleton"
        >
          <div style="display: flex; align-items: center; justify-content: space-between; gap: 0.75rem;">
            <MarketBadge :market="market" />
            <span class="spinner market-status-spinner" />
          </div>
          <div class="text-muted" style="margin-top: 1rem; font-size: 0.85rem;">
            Loading status...
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="loadError" class="text-muted">
      {{ loadError }}
    </div>

    <div v-else class="grid grid-4 market-status-grid">
      <div
        v-for="market in markets"
        :key="market"
        class="card"
      >
        <div style="display: flex; justify-content: space-between; align-items: center; gap: 0.75rem;">
          <div style="display: flex; align-items: center; gap: 0.5rem;">
            <MarketBadge :market="market" />
          </div>
          <span
            class="badge"
            :class="statusByMarket[market]?.open ? 'badge-success' : 'badge-warning'"
          >
            {{ statusByMarket[market]?.open ? 'Open' : 'Closed' }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import MarketBadge from '@/components/MarketBadge.vue'
import { getMarketStatus } from '@/api/markets'
import type { MarketStatus } from '@/types'

const markets = ['BR', 'US', 'UK', 'EU']
const loading = ref(true)
const loadError = ref('')
const statusByMarket = ref<MarketStatus>({})

onMounted(async () => {
  try {
    statusByMarket.value = await getMarketStatus()
  } catch {
    loadError.value = 'Market status is unavailable right now.'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.market-status-grid {
  align-items: stretch;
}

.market-status-skeleton {
  min-height: 7rem;
}

.market-status-spinner {
  width: 1rem;
  height: 1rem;
  flex: 0 0 auto;
}

.market-status-section {
  margin-top: 2rem;
}
</style>
