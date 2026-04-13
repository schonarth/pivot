import { defineStore } from 'pinia'
import { ref } from 'vue'

export type ToastType = 'info' | 'success' | 'warning' | 'error'

export interface Toast {
  id: string
  type: ToastType
  message: string
  duration?: number | null
}

export const useToastStore = defineStore('toasts', () => {
  const toasts = ref<Toast[]>([])

  function addToast(type: ToastType, message: string, duration?: number | null) {
    const id = Math.random().toString(36).substr(2, 9)
    toasts.value.push({ id, type, message, duration })
    return id
  }

  function removeToast(id: string) {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  return { toasts, addToast, removeToast }
})
