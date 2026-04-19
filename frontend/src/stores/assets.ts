import { defineStore } from 'pinia'
import { ref } from 'vue'

export type AssetSortKey = 'display_symbol' | 'name' | 'market' | 'currency' | 'sector'
export type AssetSortDirection = 'asc' | 'desc'

export const useAssetStore = defineStore('assets', () => {
  const marketFilter = ref('')
  const sortKey = ref<AssetSortKey>('display_symbol')
  const sortDir = ref<AssetSortDirection>('asc')

  function toggleMarket(code: string) {
    marketFilter.value = marketFilter.value === code ? '' : code
  }

  function setSort(nextKey: AssetSortKey) {
    if (sortKey.value === nextKey) {
      sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
      return
    }

    sortKey.value = nextKey
    sortDir.value = 'asc'
  }

  return {
    marketFilter,
    sortKey,
    sortDir,
    toggleMarket,
    setSort,
  }
})
