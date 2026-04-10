<template>
  <div>
    <div class="page-header">
      <h1>Assets</h1>
    </div>
    <div class="card" style="margin-bottom: 1rem;">
      <div style="display: flex; gap: 1rem;">
        <div class="form-group" style="flex: 1; margin-bottom: 0;">
          <input v-model="search" type="text" placeholder="Search assets..." @input="debouncedSearch" />
        </div>
        <div class="form-group" style="width: 150px; margin-bottom: 0;">
          <select v-model="marketFilter" @change="doSearch">
            <option value="">All</option>
            <option value="BR">Brazil</option>
            <option value="US">US</option>
            <option value="UK">UK</option>
            <option value="EU">EU</option>
          </select>
        </div>
      </div>
    </div>
    <div v-if="loading" style="text-align: center; padding: 2rem;"><span class="spinner"></span></div>
    <div v-else-if="assets.length" class="card">
      <table>
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Name</th>
            <th>Market</th>
            <th>Currency</th>
            <th>Sector</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="asset in assets" :key="asset.id" @click="$router.push(`/assets/${asset.id}`)" style="cursor: pointer;">
            <td><strong>{{ asset.display_symbol }}</strong></td>
            <td>{{ asset.name }}</td>
            <td><span class="badge badge-info">{{ asset.market }}</span></td>
            <td>{{ asset.currency }}</td>
            <td>{{ asset.sector || '-' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="card"><p class="text-muted">No assets found. Try a different search.</p></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { searchAssets } from '@/api/assets'
import type { Asset } from '@/types'

const search = ref('')
const marketFilter = ref('')
const assets = ref<Asset[]>([])
const loading = ref(false)

onMounted(doSearch)

let timeout: ReturnType<typeof setTimeout>
function debouncedSearch() {
  clearTimeout(timeout)
  timeout = setTimeout(doSearch, 300)
}

async function doSearch() {
  loading.value = true
  try {
    assets.value = await searchAssets(search.value, marketFilter.value || undefined)
  } finally {
    loading.value = false
  }
}
</script>