<template>
  <div>
    <div class="page-header">
      <h1>Dashboard</h1>
      <router-link
        to="/portfolios/new"
        class="btn"
      >
        New Portfolio
      </router-link>
    </div>

    <h2 style="margin-bottom: 1rem;">
      Portfolios
    </h2>

    <div
      v-if="portfolioStore.loading"
      class="grid grid-3"
    >
      <div
        v-for="i in 3"
        :key="i"
        class="card"
      >
        <div class="dashboard-portfolio-skeleton">
          <div class="dashboard-portfolio-skeleton-row dashboard-portfolio-skeleton-title" />
          <div class="dashboard-portfolio-skeleton-row" />
          <div class="dashboard-portfolio-skeleton-row" />
          <div class="dashboard-portfolio-skeleton-row" />
        </div>
      </div>
    </div>
    <div
      v-else-if="validPortfolios.length"
      class="grid grid-3"
    >
      <PortfolioCard
        v-for="p in validPortfolios"
        :key="p.id"
        :portfolio="p"
      />
    </div>
    <div
      v-else
      class="card"
    >
      <p class="text-muted">
        No portfolios yet. Create one to get started!
      </p>
    </div>

    <MarketStatusPanel />
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { usePortfolioStore } from '@/stores/portfolios'
import { storeToRefs } from 'pinia'
import MarketStatusPanel from '@/components/MarketStatusPanel.vue'
import PortfolioCard from '@/components/PortfolioCard.vue'

const portfolioStore = usePortfolioStore()
const { portfolios } = storeToRefs(portfolioStore)
const validPortfolios = computed(() => portfolios.value.filter((p) => Boolean(p.id) && p.id !== 'undefined'))

onMounted(async () => {
  await portfolioStore.fetchPortfolios()
})
</script>

<style scoped>
.dashboard-portfolio-skeleton {
  display: grid;
  gap: 0.6rem;
}

.dashboard-portfolio-skeleton-row {
  height: 0.9rem;
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(148, 163, 184, 0.15), rgba(148, 163, 184, 0.28), rgba(148, 163, 184, 0.15));
  background-size: 200% 100%;
  animation: dashboard-portfolio-shimmer 1.2s ease-in-out infinite;
}

.dashboard-portfolio-skeleton-title {
  width: 60%;
}

@keyframes dashboard-portfolio-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
