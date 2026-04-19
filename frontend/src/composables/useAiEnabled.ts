import { onMounted, onUnmounted, ref } from 'vue'
import { getSettings } from '@/api/ai'

export function useAiEnabled() {
  const aiEnabled = ref(true)

  async function refreshAiEnabled() {
    try {
      const settings = await getSettings()
      aiEnabled.value = settings.enabled
    } catch {
      aiEnabled.value = true
    }
  }

  onMounted(() => {
    void refreshAiEnabled()
    window.addEventListener('ai-budget-changed', refreshAiEnabled)
  })

  onUnmounted(() => {
    window.removeEventListener('ai-budget-changed', refreshAiEnabled)
  })

  return {
    aiEnabled,
    refreshAiEnabled,
  }
}
