<template>
  <div class="toast" :class="`toast-${type}`">
    <div class="toast-content">{{ message }}</div>
    <button class="toast-close" @click="emit('close')" aria-label="Close notification">×</button>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useToastStore } from '@/stores/toasts'
import type { ToastType } from '@/stores/toasts'

const props = defineProps<{
  id: string
  type: ToastType
  message: string
  duration?: number | null
}>()

const emit = defineEmits<{
  close: []
}>()

const toastStore = useToastStore()

onMounted(() => {
  if (props.duration !== null && typeof props.duration === 'number' && props.duration > 0) {
    setTimeout(() => {
      toastStore.removeToast(props.id)
    }, props.duration * 1000)
  }
})
</script>

<style scoped>
.toast {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem;
  border-radius: 0.5rem;
  margin-bottom: 0.5rem;
  animation: slideIn 0.3s ease-out;
  max-width: 400px;
}

@keyframes slideIn {
  from {
    transform: translateX(400px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.toast-content {
  flex: 1;
  font-size: 0.875rem;
}

.toast-close {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.5rem;
  line-height: 1;
  color: inherit;
  opacity: 0.7;
  padding: 0;
  width: 1.5rem;
  height: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.toast-close:hover {
  opacity: 1;
}

.toast-info {
  background: var(--toast-info-bg, #e3f2fd);
  color: var(--toast-info-text, #0d47a1);
  border-left: 4px solid var(--toast-info-border, #2196f3);
}

.toast-success {
  background: var(--toast-success-bg, #e8f5e9);
  color: var(--toast-success-text, #1b5e20);
  border-left: 4px solid var(--toast-success-border, #4caf50);
}

.toast-warning {
  background: var(--toast-warning-bg, #fff3e0);
  color: var(--toast-warning-text, #e65100);
  border-left: 4px solid var(--toast-warning-border, #ff9800);
}

.toast-error {
  background: var(--toast-error-bg, #ffebee);
  color: var(--toast-error-text, #b71c1c);
  border-left: 4px solid var(--toast-error-border, #f44336);
}
</style>
