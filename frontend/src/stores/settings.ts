import { defineStore } from 'pinia'
import { ref } from 'vue'

export type MarketBadgeStyle = 'code' | 'flag' | 'both'
export type ToastSetting = 'none' | 'disappear' | 'stay'

export const useSettingsStore = defineStore('settings', () => {
  const theme = ref<string>(localStorage.getItem('theme') ?? 'dark')
  const marketBadgeStyle = ref<MarketBadgeStyle>(
    (localStorage.getItem('marketBadgeStyle') as MarketBadgeStyle) ?? 'both'
  )
  const toastSetting = ref<ToastSetting>(
    (localStorage.getItem('toastSetting') as ToastSetting) ?? 'disappear'
  )
  const toastDuration = ref<number>(parseInt(localStorage.getItem('toastDuration') ?? '30'))

  function setTheme(t: string) {
    theme.value = t
    localStorage.setItem('theme', t)
    document.documentElement.setAttribute('data-theme', t)
  }

  function setMarketBadgeStyle(s: MarketBadgeStyle) {
    marketBadgeStyle.value = s
    localStorage.setItem('marketBadgeStyle', s)
  }

  function setToastSetting(s: ToastSetting) {
    toastSetting.value = s
    localStorage.setItem('toastSetting', s)
  }

  function setToastDuration(d: number) {
    toastDuration.value = d
    localStorage.setItem('toastDuration', d.toString())
  }

  function init() {
    document.documentElement.setAttribute('data-theme', theme.value)
  }

  return { theme, marketBadgeStyle, toastSetting, toastDuration, setTheme, setMarketBadgeStyle, setToastSetting, setToastDuration, init }
})
