import { defineStore } from 'pinia'
import { ref } from 'vue'

export const DISCOVERY_MARKETS = ['BR', 'EU', 'US', 'UK'] as const
export type DiscoveryMarket = (typeof DISCOVERY_MARKETS)[number]

export const useDiscoveryStore = defineStore('discovery', () => {
  const selectedMarket = ref<DiscoveryMarket>('US')

  function setMarket(market: DiscoveryMarket) {
    selectedMarket.value = market
  }

  return {
    selectedMarket,
    setMarket,
  }
})
