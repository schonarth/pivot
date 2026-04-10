import { ref, onUnmounted } from 'vue'

const WS_URL = import.meta.env.VITE_WS_URL || `ws://${window.location.host}/ws/portfolio/`

interface WSMessage {
  type: string
  [key: string]: unknown
}

export function useWebSocket() {
  const ws = ref<WebSocket | null>(null)
  const connected = ref(false)
  const lastMessage = ref<WSMessage | null>(null)
  const listeners = new Map<string, (data: WSMessage) => void>()
  let reconnectAttempts = 0
  const maxReconnectAttempts = 10
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null

  function connect() {
    const token = localStorage.getItem('access_token')
    if (!token) return

    const url = `${WS_URL}?token=${token}`
    ws.value = new WebSocket(url)

    ws.value.onopen = () => {
      connected.value = true
      reconnectAttempts = 0
    }

    ws.value.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WSMessage
        lastMessage.value = data
        const handler = listeners.get(data.type)
        if (handler) handler(data)
      } catch {
        // ignore malformed messages
      }
    }

    ws.value.onclose = () => {
      connected.value = false
      scheduleReconnect()
    }

    ws.value.onerror = () => {
      connected.value = false
    }
  }

  function scheduleReconnect() {
    if (reconnectAttempts >= maxReconnectAttempts) return
    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000)
    reconnectTimer = setTimeout(() => {
      reconnectAttempts++
      connect()
    }, delay)
  }

  function subscribe(portfolioIds: string[]) {
    if (!ws.value || ws.value.readyState !== WebSocket.OPEN) return
    portfolioIds.forEach((id) => {
      ws.value!.send(JSON.stringify({ action: 'subscribe_portfolio', portfolio_id: id }))
    })
  }

  function unsubscribe(portfolioIds: string[]) {
    if (!ws.value || ws.value.readyState !== WebSocket.OPEN) return
    portfolioIds.forEach((id) => {
      ws.value!.send(JSON.stringify({ action: 'unsubscribe_portfolio', portfolio_id: id }))
    })
  }

  function on(type: string, handler: (data: WSMessage) => void) {
    listeners.set(type, handler)
  }

  function off(type: string) {
    listeners.delete(type)
  }

  function disconnect() {
    if (reconnectTimer) clearTimeout(reconnectTimer)
    ws.value?.close()
    ws.value = null
    connected.value = false
  }

  onUnmounted(() => {
    disconnect()
  })

  return {
    connected,
    lastMessage,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    on,
    off,
  }
}