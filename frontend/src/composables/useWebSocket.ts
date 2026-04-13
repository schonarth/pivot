import { ref } from 'vue'

const WS_URL = (() => {
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
  return `${protocol}://${window.location.host}/ws/portfolio/`
})()

interface WSMessage {
  type: string
  [key: string]: unknown
}

// Module-level singleton — one socket for the lifetime of the app
const ws = ref<WebSocket | null>(null)
const connected = ref(false)
const listeners = new Map<string, (data: WSMessage) => void>()
let reconnectAttempts = 0
const maxReconnectAttempts = 10
let reconnectTimer: ReturnType<typeof setTimeout> | null = null

function connect() {
  if (ws.value && ws.value.readyState === WebSocket.OPEN) return

  const token = localStorage.getItem('access_token')
  if (!token) return

  try {
    ws.value = new WebSocket(`${WS_URL}?token=${token}`)
  } catch (err) {
    console.error('[WS] Failed to create WebSocket:', err)
    return
  }

  ws.value.onopen = () => {
    connected.value = true
    reconnectAttempts = 0
  }

  ws.value.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data) as WSMessage
      const handler = listeners.get(data.type)
      if (handler) handler(data)
    } catch (err) {
      console.warn('[WS] Failed to parse message:', err)
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
  const attemptSubscribe = () => {
    if (!ws.value || ws.value.readyState !== WebSocket.OPEN) {
      setTimeout(attemptSubscribe, 100)
      return
    }
    portfolioIds.forEach((id) => {
      ws.value!.send(JSON.stringify({ action: 'subscribe_portfolio', portfolio_id: id }))
    })
  }
  attemptSubscribe()
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
  reconnectTimer = null
  ws.value?.close()
  ws.value = null
  connected.value = false
  reconnectAttempts = 0
}

export function useWebSocket() {
  return { connected, connect, disconnect, subscribe, unsubscribe, on, off }
}
