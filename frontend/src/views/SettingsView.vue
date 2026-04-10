<template>
  <div>
    <div class="page-header">
      <h1>Settings</h1>
    </div>
    <div class="card" style="max-width: 500px;">
      <h3>Theme</h3>
      <div style="display: flex; gap: 1rem; margin: 1rem 0;">
        <button class="btn" :class="{ 'btn-secondary': theme !== 'dark' }" @click="setTheme('dark')">Dark</button>
        <button class="btn" :class="{ 'btn-secondary': theme !== 'light' }" @click="setTheme('light')">Light</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const theme = ref('dark')

onMounted(() => {
  const saved = localStorage.getItem('theme')
  if (saved) {
    theme.value = saved
    applyTheme(saved)
  }
})

function setTheme(t: string) {
  theme.value = t
  localStorage.setItem('theme', t)
  applyTheme(t)
}

function applyTheme(t: string) {
  document.documentElement.setAttribute('data-theme', t)
}
</script>