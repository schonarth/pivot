<template>
  <div>
    <div class="page-header">
      <h1>Settings</h1>
    </div>
    <div class="settings-container">
      <div class="settings-left">
        <div class="card">
          <h3>Theme</h3>
          <div style="display: flex; gap: 1rem; margin: 1rem 0;">
            <button class="btn" :class="{ 'btn-secondary': settings.theme !== 'dark' }" @click="settings.setTheme('dark')">Dark</button>
            <button class="btn" :class="{ 'btn-secondary': settings.theme !== 'light' }" @click="settings.setTheme('light')">Light</button>
          </div>
        </div>
        <div class="card">
          <h3>Market Badges</h3>
          <div style="display: flex; gap: 1rem; margin: 1rem 0;">
            <button class="btn" :class="{ 'btn-secondary': settings.marketBadgeStyle !== 'code' }" @click="settings.setMarketBadgeStyle('code')">2-letter</button>
            <button class="btn" :class="{ 'btn-secondary': settings.marketBadgeStyle !== 'flag' }" @click="settings.setMarketBadgeStyle('flag')">Flag</button>
            <button class="btn" :class="{ 'btn-secondary': settings.marketBadgeStyle !== 'both' }" @click="settings.setMarketBadgeStyle('both')">Both</button>
          </div>
        </div>
        <div class="card">
          <h3>Alert Toasts</h3>
          <div style="display: flex; gap: 1rem; margin: 1rem 0;">
            <button class="btn" :class="{ 'btn-secondary': settings.toastSetting !== 'none' }" @click="settings.setToastSetting('none')">None</button>
            <button class="btn" :class="{ 'btn-secondary': settings.toastSetting !== 'disappear' }" @click="settings.setToastSetting('disappear')">Disappear</button>
            <button class="btn" :class="{ 'btn-secondary': settings.toastSetting !== 'stay' }" @click="settings.setToastSetting('stay')">Stay</button>
          </div>
          <div v-if="settings.toastSetting === 'disappear'" style="margin-top: 1rem;">
            <label>Disappear after (seconds):</label>
            <input
              type="number"
              min="1"
              max="300"
              :value="settings.toastDuration"
              @change="(e) => settings.setToastDuration(parseInt((e.target as HTMLInputElement).value))"
              style="margin-top: 0.5rem; width: 100%; padding: 0.5rem; border-radius: 0.25rem; border: 1px solid var(--border);"
            />
          </div>
          <div style="margin-top: 1rem;">
            <button class="btn btn-secondary" @click="sendTestNotifications">Send Test Notifications</button>
          </div>
        </div>
      </div>
      <div class="settings-right">
        <MCPSettings />
      </div>
    </div>
  </div>
</template>

<style scoped>
.settings-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}

.settings-left,
.settings-right {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

@media (max-width: 1024px) {
  .settings-container {
    grid-template-columns: 1fr;
  }
}
</style>

<script setup lang="ts">
import { useSettingsStore } from '@/stores/settings'
import { useToast } from '@/composables/useToast'
import { useNotifications } from '@/composables/useNotifications'
import MCPSettings from '@/components/MCPSettings.vue'

const settings = useSettingsStore()
const toast = useToast()
const { showNotification } = useNotifications()

async function sendTestNotifications() {
  toast.success('Success notification')
  toast.warning('Warning notification')
  toast.info('Info notification')
  toast.error('Error notification')

  showNotification('Test Browser Notification', {
    body: 'This is a browser notification test',
    icon: '/icon.png',
  })
}
</script>
