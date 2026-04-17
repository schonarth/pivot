<template>
  <div class="card">
    <div class="section-header">
      <div>
        <h3>Asset Analysis History Backfill</h3>
        <p class="text-muted">
          Rebuild historical price bars for seeded assets.
        </p>
      </div>
      <button
        class="btn btn-secondary"
        :disabled="starting || isActive"
        @click="startBackfill"
      >
        {{ starting ? 'Starting...' : (isActive ? 'Backfill Running' : 'Start Backfill') }}
      </button>
    </div>

    <div class="status-row">
      <span class="badge" :class="stateClass">
        {{ statusLabel }}
      </span>
      <span class="text-muted">
        {{ status.total_assets }} assets
      </span>
      <span class="text-muted">
        {{ status.successful_assets }} done, {{ status.failed_assets }} failed
      </span>
    </div>

    <div class="progress-shell" aria-label="OHLCV backfill progress">
      <div class="progress-bar" :style="{ width: `${progressPercent}%` }" />
    </div>

    <div class="text-muted" style="margin-bottom: 0.75rem;">
      {{ status.processed_assets_count }} / {{ status.total_assets }} processed
      <span v-if="currentAsset">
        · Currently fetching {{ currentAsset.symbol }} ({{ currentAsset.index }}/{{ currentAsset.total_assets }})
      </span>
    </div>

    <div class="log-shell">
      <div class="log-title">
        Processed assets
      </div>
      <ul class="log-list">
        <li
          v-for="item in status.processed_assets"
          :key="`${item.timestamp}-${item.symbol}`"
          :class="item.status"
        >
          <strong>{{ item.symbol }}</strong>
          <span v-if="item.status === 'completed'">
            · {{ item.rows_ingested ?? 0 }} rows ingested
          </span>
          <span v-else>
            · {{ item.error || 'Failed' }}
          </span>
        </li>
        <li v-if="status.processed_assets.length === 0" class="text-muted">
          No assets processed yet.
        </li>
      </ul>
    </div>

    <div v-if="error" class="text-muted" style="margin-top: 0.75rem;">
      {{ error }}
    </div>

    <div class="divider" />

    <details class="repair-details">
      <summary>
        <span class="chevron-triangle" aria-hidden="true" />
        <span>Repair Malformed OHLCV Bars</span>
      </summary>

      <div class="repair-panel">
        <div class="repair-form">
          <label class="field">
            <span>Asset symbol</span>
            <input v-model="repairSymbol" type="text" placeholder="PETR4" />
          </label>
          <label class="field">
            <span>From</span>
            <input v-model="repairDateFrom" type="date" />
          </label>
          <label class="field">
            <span>To</span>
            <input v-model="repairDateTo" type="date" />
          </label>
        </div>

        <div class="section-header compact">
          <div class="status-row">
            <span class="badge" :class="repairStateClass">
              {{ repairStatusLabel }}
            </span>
            <span class="text-muted">
              {{ repairStatus.total_assets }} assets
            </span>
            <span class="text-muted">
              {{ repairStatus.invalid_rows_deleted }} rows removed
            </span>
            <span class="text-muted">
              {{ repairStatus.repaired_rows }} rows restored
            </span>
          </div>
          <button
            class="btn btn-secondary"
            :disabled="repairStarting || repairIsActive"
            @click="startRepair"
          >
            {{ repairStarting ? 'Starting...' : (repairIsActive ? 'Repair Running' : 'Search and Repair') }}
          </button>
        </div>

        <div class="progress-shell" aria-label="OHLCV repair progress">
          <div class="progress-bar" :style="{ width: `${repairProgressPercent}%` }" />
        </div>

        <div class="text-muted" style="margin-bottom: 0.75rem;">
          {{ repairStatus.processed_assets_count }} / {{ repairStatus.total_assets }} processed
          <span v-if="repairCurrentAsset">
            · Currently checking {{ repairCurrentAsset.symbol }} ({{ repairCurrentAsset.index }}/{{ repairCurrentAsset.total_assets }})
          </span>
        </div>

        <div class="log-shell">
          <div class="log-title">
            Repaired assets
          </div>
          <ul class="log-list">
            <li
              v-for="item in repairStatus.processed_assets"
              :key="`${item.timestamp}-${item.symbol}`"
              :class="item.status"
            >
              <strong>{{ item.symbol }}</strong>
              <span v-if="item.status === 'completed'">
                · {{ item.invalid_rows_deleted ?? 0 }} rows removed, {{ item.rows_ingested ?? 0 }} rows restored
              </span>
              <span v-else>
                · {{ item.error || 'Failed' }}
              </span>
            </li>
            <li v-if="repairStatus.processed_assets.length === 0" class="text-muted">
              No assets processed yet.
            </li>
          </ul>
        </div>

        <div v-if="repairError" class="text-muted" style="margin-top: 0.75rem;">
          {{ repairError }}
        </div>
      </div>
    </details>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { getOhlcvBackfillStatus, getOhlcvRepairStatus, startOhlcvBackfill, startOhlcvRepair } from '@/api/markets'
import type { OhlcvBackfillStatus, OhlcvRepairStatus } from '@/types'
import { useWebSocketStore } from '@/stores/websocket'

const ws = useWebSocketStore()
const starting = ref(false)
const error = ref('')
const repairError = ref('')
const repairStarting = ref(false)
const repairSymbol = ref('')
const repairDateFrom = ref('')
const repairDateTo = ref('')
const status = ref<OhlcvBackfillStatus>({
  state: 'idle',
  source: null,
  initiated_by: null,
  total_assets: 0,
  processed_assets_count: 0,
  successful_assets: 0,
  failed_assets: 0,
  current_asset: null,
  processed_assets: [],
  started_at: null,
  updated_at: new Date().toISOString(),
  completed_at: null,
})
const repairStatus = ref<OhlcvRepairStatus>({
  state: 'idle',
  source: null,
  initiated_by: null,
  symbol: null,
  date_from: null,
  date_to: null,
  total_assets: 0,
  processed_assets_count: 0,
  invalid_rows_found: 0,
  invalid_rows_deleted: 0,
  repaired_rows: 0,
  current_asset: null,
  processed_assets: [],
  started_at: null,
  updated_at: new Date().toISOString(),
  completed_at: null,
})

const isActive = computed(() => ['queued', 'running'].includes(status.value.state))
const currentAsset = computed(() => status.value.current_asset)
const progressPercent = computed(() => {
  if (!status.value.total_assets) return 0
  return Math.min(100, Math.round((status.value.processed_assets_count / status.value.total_assets) * 100))
})
const statusLabel = computed(() => {
  const labels: Record<OhlcvBackfillStatus['state'], string> = {
    idle: 'Idle',
    queued: 'Queued',
    running: 'Running',
    completed: 'Completed',
    failed: 'Failed',
  }
  return labels[status.value.state]
})
const stateClass = computed(() => ({
  'badge-secondary': status.value.state === 'idle',
  'badge-warning': status.value.state === 'queued',
  'badge-info': status.value.state === 'running',
  'badge-success': status.value.state === 'completed',
  'badge-danger': status.value.state === 'failed',
}))
const repairIsActive = computed(() => ['queued', 'running'].includes(repairStatus.value.state))
const repairCurrentAsset = computed(() => repairStatus.value.current_asset)
const repairProgressPercent = computed(() => {
  if (!repairStatus.value.total_assets) return 0
  return Math.min(100, Math.round((repairStatus.value.processed_assets_count / repairStatus.value.total_assets) * 100))
})
const repairStatusLabel = computed(() => {
  const labels: Record<OhlcvRepairStatus['state'], string> = {
    idle: 'Idle',
    queued: 'Queued',
    running: 'Running',
    completed: 'Completed',
    failed: 'Failed',
  }
  return labels[repairStatus.value.state]
})
const repairStateClass = computed(() => ({
  'badge-secondary': repairStatus.value.state === 'idle',
  'badge-warning': repairStatus.value.state === 'queued',
  'badge-info': repairStatus.value.state === 'running',
  'badge-success': repairStatus.value.state === 'completed',
  'badge-danger': repairStatus.value.state === 'failed',
}))

function applyStatus(nextStatus: OhlcvBackfillStatus) {
  status.value = nextStatus
  error.value = ''
}

function applyRepairStatus(nextStatus: OhlcvRepairStatus) {
  repairStatus.value = nextStatus
  repairError.value = ''
}

async function loadStatus() {
  try {
    applyStatus(await getOhlcvBackfillStatus())
  } catch (err) {
    error.value = 'Failed to load OHLCV backfill status.'
  }
}

async function loadRepairStatus() {
  try {
    applyRepairStatus(await getOhlcvRepairStatus())
  } catch (err) {
    repairError.value = 'Failed to load OHLCV repair status.'
  }
}

async function startBackfill() {
  starting.value = true
  error.value = ''
  try {
    applyStatus(await startOhlcvBackfill())
  } catch (err) {
    error.value = 'Failed to start OHLCV backfill.'
  } finally {
    starting.value = false
  }
}

async function startRepair() {
  repairStarting.value = true
  repairError.value = ''
  try {
    applyRepairStatus(await startOhlcvRepair({
      symbol: repairSymbol.value.trim() || null,
      date_from: repairDateFrom.value || null,
      date_to: repairDateTo.value || null,
    }))
  } catch (err) {
    repairError.value = 'Failed to start OHLCV repair.'
  } finally {
    repairStarting.value = false
  }
}

function handleUpdate(nextStatus: OhlcvBackfillStatus) {
  applyStatus(nextStatus)
}

function handleRepairUpdate(nextStatus: OhlcvRepairStatus) {
  applyRepairStatus(nextStatus)
}

onMounted(async () => {
  ws.startConnection()
  ws.on('ohlcv.backfill.updated', handleUpdate)
  ws.on('ohlcv.backfill.completed', handleUpdate)
  ws.on('ohlcv.backfill.failed', handleUpdate)
  ws.on('ohlcv.repair.updated', handleRepairUpdate)
  ws.on('ohlcv.repair.completed', handleRepairUpdate)
  ws.on('ohlcv.repair.failed', handleRepairUpdate)
  await loadStatus()
  await loadRepairStatus()
})

onBeforeUnmount(() => {
  ws.off('ohlcv.backfill.updated')
  ws.off('ohlcv.backfill.completed')
  ws.off('ohlcv.backfill.failed')
  ws.off('ohlcv.repair.updated')
  ws.off('ohlcv.repair.completed')
  ws.off('ohlcv.repair.failed')
})
</script>

<style scoped>
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.status-row {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  align-items: center;
  margin: 1rem 0;
}

.progress-shell {
  height: 0.75rem;
  border-radius: 999px;
  background: var(--border);
  overflow: hidden;
  margin-bottom: 0.75rem;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), var(--accent-hover));
  transition: width 0.25s ease;
}

.log-shell {
  border: 1px solid var(--border);
  border-radius: 0.75rem;
  padding: 0.75rem;
  background: var(--bg-secondary);
}

.log-title {
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}

.log-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 0.5rem;
}

.log-list li {
  padding: 0.5rem 0.75rem;
  border-radius: 0.5rem;
  background: var(--bg-tertiary);
}

.log-list li.completed {
  border-left: 3px solid var(--success);
}

.log-list li.failed {
  border-left: 3px solid var(--danger);
}

.divider {
  height: 1px;
  background: var(--border);
  margin: 1.5rem 0;
}

.repair-form {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.75rem;
  margin: 1rem 0;
}

.field {
  display: grid;
  gap: 0.35rem;
}

.field span {
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-muted);
}

.field input {
  width: 100%;
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  padding: 0.625rem 0.75rem;
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.repair-details {
  margin-top: 0.75rem;
}

.repair-details summary {
  cursor: pointer;
  color: var(--text-primary);
  font-size: 1rem;
  margin-bottom: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  list-style: none;
}

.repair-details summary::-webkit-details-marker {
  display: none;
}

.chevron-triangle {
  width: 0;
  height: 0;
  border-top: 0.35rem solid transparent;
  border-bottom: 0.35rem solid transparent;
  border-left: 0.5rem solid currentColor;
  transition: transform 0.2s ease;
  flex: none;
}

.repair-details[open] .chevron-triangle {
  transform: rotate(90deg);
}

.repair-panel {
  display: grid;
  gap: 1rem;
}

.compact {
  margin-top: 0;
}

@media (max-width: 720px) {
  .repair-form {
    grid-template-columns: 1fr;
  }
}
</style>
