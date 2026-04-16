<template>
  <div class="card">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem;">
      <div>
        <h3 style="margin-bottom: 0.25rem;">
          {{ title }}
        </h3>
        <div class="text-muted" style="font-size: 0.75rem;">
          {{ scopeLabel }} · {{ assets.length }} assets
        </div>
      </div>
      <span class="badge badge-secondary">
        Monitored Set
      </span>
    </div>

    <div
      v-if="!assets.length"
      class="text-muted"
      style="margin-top: 1rem;"
    >
      {{ emptyMessage }}
    </div>

    <template v-else>
      <div class="asset-pills">
        <div
          v-for="asset in assets"
          :key="asset.asset_id"
          class="asset-pill"
          :class="{ active: asset.asset_id === selectedAssetId }"
        >
          <button
            class="asset-pill-main"
            @click="selectedAssetId = asset.asset_id"
          >
            <strong>{{ asset.symbol }}</strong>
            <span class="text-muted">{{ asset.name }}</span>
          </button>
          <button
            v-if="allowRemoval"
            class="asset-pill-remove"
            title="Remove from watch"
            @click.stop="emit('remove', asset.asset_id)"
          >
            Remove
          </button>
        </div>
      </div>

      <div v-if="selectedAsset">
        <div class="text-muted" style="font-size: 0.75rem; margin-bottom: 0.75rem;">
          {{ selectedAsset.symbol }} · {{ selectedAsset.name }}
          <span v-if="selectedAsset.current_price !== null">
            · {{ selectedAsset.currency }} {{ formatNum(selectedAsset.current_price) }}
          </span>
        </div>
        <AssetAnalysisTab :key="selectedAsset.asset_id" :asset-id="selectedAsset.asset_id" />
        <div style="margin-top: 0.75rem;">
          <router-link
            :to="`/assets/${selectedAsset.asset_id}`"
            class="btn btn-secondary btn-sm"
          >
            Open Asset Detail
          </router-link>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import AssetAnalysisTab from '@/components/AssetAnalysisTab.vue'
import { formatCurrency } from '@/utils/numbers'
import type { MonitoredAssetSummary } from '@/types'

const props = defineProps<{
  title: string
  scopeLabel: string
  emptyMessage: string
  assets: MonitoredAssetSummary[]
  allowRemoval?: boolean
}>()

const emit = defineEmits<{
  (e: 'remove', assetId: string): void
}>()

const selectedAssetId = ref('')

const selectedAsset = computed(() => props.assets.find((asset) => asset.asset_id === selectedAssetId.value) ?? null)

watch(
  () => props.assets,
  (assets) => {
    if (!assets.length) {
      selectedAssetId.value = ''
      return
    }
    if (!selectedAssetId.value || !assets.some((asset) => asset.asset_id === selectedAssetId.value)) {
      selectedAssetId.value = assets[0].asset_id
    }
  },
  { immediate: true },
)

function formatNum(value: string | null): string {
  if (value === null) return '-'
  return formatCurrency(value)
}
</script>

<style scoped>
.asset-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 1rem;
  margin-bottom: 1rem;
}

.asset-pill {
  display: flex;
  align-items: stretch;
  border: 1px solid var(--border);
  background: transparent;
  color: var(--text);
  border-radius: 8px;
  overflow: hidden;
  min-width: 9rem;
}

.asset-pill.active {
  border-color: var(--accent);
  background: rgba(59, 130, 246, 0.08);
}

.asset-pill-main {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  text-align: left;
  border: 0;
  background: transparent;
  color: inherit;
  padding: 0.6rem 0.75rem;
  cursor: pointer;
}

.asset-pill-remove {
  border: 0;
  border-top: 1px solid var(--border);
  background: rgba(239, 68, 68, 0.08);
  color: var(--text);
  padding: 0.35rem 0.75rem;
  cursor: pointer;
  font-size: 0.8rem;
}
</style>
