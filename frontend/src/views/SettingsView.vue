<template>
  <div>
    <div class="page-header">
      <h1>Settings</h1>
    </div>
    <div class="card" style="max-width: 500px;">
      <h3>Theme</h3>
      <div style="display: flex; gap: 1rem; margin: 1rem 0;">
        <button class="btn" :class="{ 'btn-secondary': settings.theme !== 'dark' }" @click="settings.setTheme('dark')">Dark</button>
        <button class="btn" :class="{ 'btn-secondary': settings.theme !== 'light' }" @click="settings.setTheme('light')">Light</button>
      </div>
    </div>
    <div class="card" style="max-width: 500px;">
      <h3>Market Badges</h3>
      <div style="display: flex; gap: 1rem; margin: 1rem 0;">
        <button class="btn" :class="{ 'btn-secondary': settings.marketBadgeStyle !== 'code' }" @click="settings.setMarketBadgeStyle('code')">2-letter</button>
        <button class="btn" :class="{ 'btn-secondary': settings.marketBadgeStyle !== 'flag' }" @click="settings.setMarketBadgeStyle('flag')">Flag</button>
        <button class="btn" :class="{ 'btn-secondary': settings.marketBadgeStyle !== 'both' }" @click="settings.setMarketBadgeStyle('both')">Both</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useSettingsStore } from '@/stores/settings'

const settings = useSettingsStore()
</script>
