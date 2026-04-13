import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Portfolio, PortfolioSummary } from '@/types'
import * as portfolioApi from '@/api/portfolios'

export const usePortfolioStore = defineStore('portfolio', () => {
  const portfolios = ref<Portfolio[]>([])
  const currentSummary = ref<PortfolioSummary | null>(null)
  const loading = ref(false)

  async function fetchPortfolios() {
    loading.value = true
    try {
      portfolios.value = await portfolioApi.getPortfolios()
    } finally {
      loading.value = false
    }
  }

  async function fetchSummary(id: string) {
    currentSummary.value = await portfolioApi.getPortfolioSummary(id)
  }

  async function createPortfolio(name: string, market: string, initialCapital: string) {
    const portfolio = await portfolioApi.createPortfolio(name, market, initialCapital)
    portfolios.value.unshift(portfolio)
    return portfolio
  }

  async function deletePortfolio(id: string) {
    await portfolioApi.deletePortfolio(id)
    portfolios.value = portfolios.value.filter((p) => p.id !== id)
  }

  return { portfolios, currentSummary, loading, fetchPortfolios, fetchSummary, createPortfolio, deletePortfolio }
})