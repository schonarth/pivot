import { useToastStore, type ToastType } from '@/stores/toasts'
import { useSettingsStore } from '@/stores/settings'

export function useToast() {
  const toastStore = useToastStore()
  const settingsStore = useSettingsStore()

  function show(type: ToastType, message: string) {
    const setting = settingsStore.toastSetting

    if (setting === 'none') {
      return
    }

    if (setting === 'disappear') {
      toastStore.addToast(type, message, settingsStore.toastDuration)
    } else if (setting === 'stay') {
      toastStore.addToast(type, message, null)
    }
  }

  return {
    info: (message: string) => show('info', message),
    success: (message: string) => show('success', message),
    warning: (message: string) => show('warning', message),
    error: (message: string) => show('error', message),
  }
}
