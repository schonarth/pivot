import { defineStore } from 'pinia'
import { ref } from 'vue'

export type MarketBadgeStyle = 'code' | 'flag' | 'both'

export const useSettingsStore = defineStore('settings', () => {
  const theme = ref<string>(localStorage.getItem('theme') ?? 'dark')
  const marketBadgeStyle = ref<MarketBadgeStyle>(
    (localStorage.getItem('marketBadgeStyle') as MarketBadgeStyle) ?? 'both'
  )

  function setTheme(t: string) {
    theme.value = t
    localStorage.setItem('theme', t)
    document.documentElement.setAttribute('data-theme', t)
  }

  function setMarketBadgeStyle(s: MarketBadgeStyle) {
    marketBadgeStyle.value = s
    localStorage.setItem('marketBadgeStyle', s)
  }

  function init() {
    document.documentElement.setAttribute('data-theme', theme.value)
  }

  return { theme, marketBadgeStyle, setTheme, setMarketBadgeStyle, init }
})
