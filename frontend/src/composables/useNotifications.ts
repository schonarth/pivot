import { ref } from 'vue'

const notificationPermission = ref<NotificationPermission>('default')

export function useNotifications() {
  async function requestPermission() {
    if (!('Notification' in window)) {
      console.log('Notifications not supported')
      return false
    }

    if (Notification.permission === 'granted') {
      notificationPermission.value = 'granted'
      return true
    }

    if (Notification.permission !== 'denied') {
      try {
        const permission = await Notification.requestPermission()
        notificationPermission.value = permission
        return permission === 'granted'
      } catch {
        return false
      }
    }

    return false
  }

  async function showNotification(title: string, options?: NotificationOptions) {
    if (!('Notification' in window)) return

    if (Notification.permission === 'granted') {
      new Notification(title, options)
      return
    }

    if (Notification.permission !== 'denied') {
      const permission = await requestPermission()
      if (permission) {
        new Notification(title, options)
      }
    }
  }

  return {
    notificationPermission,
    requestPermission,
    showNotification,
  }
}
