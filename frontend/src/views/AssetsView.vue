<template>
  <div style="display: flex; flex-direction: column; height: 100%;">
    <div class="page-header">
      <h1>Assets</h1>
    </div>
    <div class="card" style="margin-bottom: 1rem; flex-shrink: 0;">
      <div style="display: flex; gap: 1rem;">
        <div class="form-group" style="flex: 1; margin-bottom: 0;">
          <input v-model="search" type="text" placeholder="Search assets..." @input="debouncedSearch" />
        </div>
        <div class="market-pills" style="margin-bottom: 0;">
          <button
            v-for="m in markets"
            :key="m.code"
            class="market-pill"
            :class="{ active: marketFilter === m.code }"
            :title="m.label"
            @click="toggleMarket(m.code)"
          >{{ m.flag }}</button>
        </div>
      </div>
    </div>

    <div v-if="loading" style="text-align: center; padding: 2rem; flex-shrink: 0;">
      <span class="spinner"></span>
    </div>
    <div v-else-if="!assets.length" class="card" style="flex-shrink: 0;">
      <p class="text-muted">No assets found. Try a different search.</p>
    </div>
    <div
      v-else
      ref="scrollEl"
      class="card"
      style="flex: 1; min-height: 0; overflow: auto; padding: 0;"
      @scroll.passive="onScroll"
    >
      <table style="table-layout: fixed; width: 100%; border-collapse: collapse;">
        <colgroup>
          <col v-for="(pct, i) in colPcts" :key="i" :style="{ width: pct }" />
        </colgroup>
        <thead>
          <tr>
            <th v-for="col in columns" :key="col.key" class="col-header" @click="setSort(col.key)">
              <span>{{ col.label }}</span>
              <span class="sort-icon">{{ sortIcon(col.key) }}</span>
              <div
                class="resize-handle"
                @mousedown.stop="startResize($event, col.index)"
              ></div>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="paddingTop > 0" :style="{ height: paddingTop + 'px' }">
            <td colspan="5" style="padding: 0; border: none;"></td>
          </tr>
          <tr
            v-for="asset in visibleAssets"
            :key="asset.id"
            :style="{ height: ROW_HEIGHT + 'px', cursor: 'pointer' }"
            @click="$router.push(`/assets/${asset.id}`)"
          >
            <td class="cell"><strong>{{ asset.display_symbol }}</strong></td>
            <td class="cell">{{ asset.name }}</td>
            <td class="cell"><MarketBadge :market="asset.market" /></td>
            <td class="cell">{{ asset.currency }}</td>
            <td class="cell">{{ asset.sector || '-' }}</td>
          </tr>
          <tr v-if="paddingBottom > 0" :style="{ height: paddingBottom + 'px' }">
            <td colspan="5" style="padding: 0; border: none;"></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { searchAssets } from '@/api/assets'
import type { Asset } from '@/types'
import MarketBadge from '@/components/MarketBadge.vue'

const ROW_HEIGHT = 48
const OVERSCAN = 5

type SortKey = 'display_symbol' | 'name' | 'market' | 'currency' | 'sector'

const columns = [
  { key: 'display_symbol' as SortKey, label: 'Symbol',   index: 0 },
  { key: 'name'           as SortKey, label: 'Name',     index: 1 },
  { key: 'market'         as SortKey, label: 'Market',   index: 2 },
  { key: 'currency'       as SortKey, label: 'Currency', index: 3 },
  { key: 'sector'         as SortKey, label: 'Sector',   index: 4 },
]

const colWidths = ref([100, 320, 80, 90, 160])
const tableWidth = computed(() => colWidths.value.reduce((s, w) => s + w, 0))
const colPcts = computed(() => colWidths.value.map(w => (w / tableWidth.value * 100).toFixed(2) + '%'))

const markets = [
  { code: 'BR', flag: '🇧🇷', label: 'BR' },
  { code: 'EU', flag: '🇪🇺', label: 'EU' },
  { code: 'US', flag: '🇺🇸', label: 'US' },
  { code: 'UK', flag: '🇬🇧', label: 'UK' },
]

const search = ref('')
const marketFilter = ref('')

function toggleMarket(code: string) {
  marketFilter.value = marketFilter.value === code ? '' : code
  doSearch()
}
const assets = ref<Asset[]>([])
const loading = ref(false)

const sortKey = ref<SortKey>('market')
const sortDir = ref<'asc' | 'desc'>('asc')

const sortedAssets = computed(() => {
  const key = sortKey.value
  return [...assets.value].sort((a, b) => {
    const av = (a[key] ?? '').toString().toLowerCase()
    const bv = (b[key] ?? '').toString().toLowerCase()
    const cmp = av.localeCompare(bv)
    return sortDir.value === 'asc' ? cmp : -cmp
  })
})

function setSort(key: SortKey) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDir.value = 'asc'
  }
  scrollTop.value = 0
  if (scrollEl.value) scrollEl.value.scrollTop = 0
}

function sortIcon(key: SortKey): string {
  if (sortKey.value !== key) return ' ⇅'
  return sortDir.value === 'asc' ? ' ↑' : ' ↓'
}

// ── Virtual scroll ──────────────────────────────────────────────────────────

const scrollEl = ref<HTMLElement | null>(null)
const scrollTop = ref(0)
const containerHeight = ref(0)

const startIndex = computed(() =>
  Math.max(0, Math.floor(scrollTop.value / ROW_HEIGHT) - OVERSCAN)
)
const endIndex = computed(() =>
  Math.min(sortedAssets.value.length, Math.ceil((scrollTop.value + containerHeight.value) / ROW_HEIGHT) + OVERSCAN)
)
const visibleAssets = computed(() => sortedAssets.value.slice(startIndex.value, endIndex.value))
const paddingTop    = computed(() => startIndex.value * ROW_HEIGHT)
const paddingBottom = computed(() => (sortedAssets.value.length - endIndex.value) * ROW_HEIGHT)

function onScroll(e: Event) {
  scrollTop.value = (e.target as HTMLElement).scrollTop
}

function measureContainer() {
  if (scrollEl.value) containerHeight.value = scrollEl.value.clientHeight
}

const resizeObserver = new ResizeObserver(measureContainer)

onMounted(async () => {
  await doSearch()
  await nextTick()
  if (scrollEl.value) {
    resizeObserver.observe(scrollEl.value)
    measureContainer()
  }
})

onUnmounted(() => {
  resizeObserver.disconnect()
  window.removeEventListener('mousemove', onResizeMove)
  window.removeEventListener('mouseup', stopResize)
})

// ── Column resize ───────────────────────────────────────────────────────────

let resizing: { colIndex: number; startX: number; startWidth: number } | null = null

function startResize(e: MouseEvent, colIndex: number) {
  resizing = { colIndex, startX: e.clientX, startWidth: colWidths.value[colIndex] }
  window.addEventListener('mousemove', onResizeMove)
  window.addEventListener('mouseup', stopResize)
  e.preventDefault()
}

function onResizeMove(e: MouseEvent) {
  if (!resizing) return
  const newWidth = Math.max(60, resizing.startWidth + (e.clientX - resizing.startX))
  colWidths.value[resizing.colIndex] = newWidth
}

function stopResize() {
  resizing = null
  window.removeEventListener('mousemove', onResizeMove)
  window.removeEventListener('mouseup', stopResize)
}

// ── Data ────────────────────────────────────────────────────────────────────

let timeout: ReturnType<typeof setTimeout>
function debouncedSearch() {
  clearTimeout(timeout)
  timeout = setTimeout(doSearch, 300)
}

async function doSearch() {
  loading.value = true
  try {
    assets.value = await searchAssets(search.value, marketFilter.value || undefined)
    scrollTop.value = 0
    if (scrollEl.value) scrollEl.value.scrollTop = 0
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.market-pills {
  display: flex;
  gap: 0.25rem;
  align-items: center;
}
.market-pill {
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  border-radius: 9999px;
  padding: 0.35rem 0.6rem;
  font-size: 1.5rem;
  cursor: pointer;
  line-height: 1;
  transition: background 0.15s, border-color 0.15s;
}
.market-pill:hover {
  border-color: var(--accent);
}
.market-pill.active {
  background: var(--accent);
  border-color: var(--accent);
}
.col-header {
  position: sticky;
  top: 0;
  background: var(--bg-secondary);
  z-index: 1;
  padding: 0.75rem 1rem;
  text-align: left;
  border-bottom: 1px solid var(--border);
  user-select: none;
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
}
.col-header:hover {
  background: var(--bg-tertiary);
}
.sort-icon {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--accent);
  font-size: 0.75rem;
}
.resize-handle {
  position: absolute;
  right: 0;
  top: 0;
  width: 6px;
  height: 100%;
  cursor: col-resize;
  background: transparent;
}
.resize-handle:hover {
  background: var(--accent);
  opacity: 0.4;
}
.cell {
  padding: 0 1rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  border-bottom: 1px solid var(--border);
}
</style>
