<template>
  <div>
    <div class="page-header">
      <h1>My Portfolios</h1>
      <router-link to="/portfolios/new" class="btn">New Portfolio</router-link>
    </div>
    <div v-if="loading" style="text-align: center; padding: 2rem;"><span class="spinner"></span></div>
    <div v-else-if="validPortfolios.length" class="grid grid-3">
      <div v-for="p in validPortfolios" :key="p.id" class="card portfolio-card" @click="$router.push(`/portfolios/${p.id}`)">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
          <strong>{{ p.name }}</strong>
          <MarketBadge :market="p.market" />
        </div>
        <div style="display: flex; justify-content: space-between;">
          <span class="text-muted">Currency</span>
          <span>{{ p.base_currency }}</span>
        </div>
        <div style="display: flex; justify-content: space-between;">
          <span class="text-muted">Initial Capital</span>
          <span>{{ p.base_currency }} {{ formatNum(p.initial_capital) }}</span>
        </div>
        <div style="display: flex; justify-content: space-between;">
          <span class="text-muted">Current Cash</span>
          <span>{{ p.base_currency }} {{ formatNum(p.current_cash) }}</span>
        </div>
        <div v-if="p.is_primary" style="margin-top: 0.5rem;">
          <span class="badge badge-success">Primary</span>
        </div>
      </div>
    </div>
    <div v-else class="card">
      <p class="text-muted">No portfolios yet. <router-link to="/portfolios/new">Create one</router-link> to get started!</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import MarketBadge from '@/components/MarketBadge.vue'
import { usePortfolioStore } from '@/stores/portfolios'
import { formatCurrency } from '@/utils/numbers'
import { storeToRefs } from 'pinia'

const portfolioStore = usePortfolioStore()
const { portfolios, loading } = storeToRefs(portfolioStore)
const validPortfolios = computed(() => portfolios.value.filter((p) => Boolean(p.id) && p.id !== 'undefined'))

onMounted(() => {
  portfolioStore.fetchPortfolios()
})

function formatNum(val: string | number, currency?: string): string {
  return formatCurrency(val, currency)
}
</script>

<style scoped>
.portfolio-card { cursor: pointer; transition: transform 0.15s; }
.portfolio-card:hover { transform: translateY(-2px); }
</style>
