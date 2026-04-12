import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { useAuthStore } from './auth'
import { useWebSocket } from '@/composables/useWebSocket'
import { getPortfolios } from '@/api/portfolios'

export const useWebSocketStore = defineStore('websocket', () => {
  const authStore = useAuthStore()
  const ws = useWebSocket()
  const subscribedPortfolios = ref(new Set<string>())

  async function subscribeToAllPortfolios() {
    try {
      const portfolios = await getPortfolios()
      const ids = portfolios.map((p: any) => p.id)
      if (ids.length > 0) {
        ids.forEach((id: string) => subscribedPortfolios.value.add(id))
        ws.subscribe(ids)
      }
    } catch (err) {
      console.error('[WebSocketStore] Failed to subscribe to all portfolios:', err)
    }
  }

  function startConnection() {
    if (!authStore.isAuthenticated) return
    ws.connect()
  }

  function stopConnection() {
    ws.disconnect()
  }

  function subscribePortfolio(portfolioId: string) {
    if (subscribedPortfolios.value.has(portfolioId)) return
    subscribedPortfolios.value.add(portfolioId)
    ws.subscribe([portfolioId])
  }

  function unsubscribePortfolio(portfolioId: string) {
    subscribedPortfolios.value.delete(portfolioId)
    ws.unsubscribe([portfolioId])
  }

  function on(type: string, handler: (data: any) => void) {
    ws.on(type, handler)
  }

  function off(type: string) {
    ws.off(type)
  }

  watch(ws.connected, (isConnected) => {
    if (isConnected) {
      subscribeToAllPortfolios()
    }
  })

  watch(
    () => authStore.isAuthenticated,
    (authenticated) => {
      if (authenticated) {
        startConnection()
      } else {
        stopConnection()
        subscribedPortfolios.value.clear()
      }
    },
    { immediate: true }
  )

  return {
    connected: ws.connected,
    subscribePortfolio,
    unsubscribePortfolio,
    on,
    off,
    startConnection,
    stopConnection,
  }
})
