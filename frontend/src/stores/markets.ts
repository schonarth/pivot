import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { MarketStatus } from '@/types'
import { getMarketStatus } from '@/api/markets'

export const useMarketStore = defineStore('market', () => {
  const status = ref<MarketStatus>({})

  async function fetchStatus() {
    status.value = await getMarketStatus()
  }

  return { status, fetchStatus }
})
