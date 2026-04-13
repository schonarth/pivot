<template>
  <div class="toast-container">
    <Toast
      v-for="toast in toastStore.toasts"
      :id="toast.id"
      :key="toast.id"
      :type="toast.type"
      :message="toast.message"
      :duration="toast.duration"
      @close="toastStore.removeToast(toast.id)"
    />
  </div>
</template>

<script setup lang="ts">
import { useToastStore } from '@/stores/toasts'
import Toast from './Toast.vue'

const toastStore = useToastStore()
</script>

<style scoped>
.toast-container {
  position: fixed;
  bottom: 1.5rem;
  right: 1.5rem;
  z-index: 9999;
  pointer-events: none;
  max-width: 450px;
}

.toast-container > * {
  pointer-events: auto;
}
</style>
