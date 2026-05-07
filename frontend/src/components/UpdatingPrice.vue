<template>
  <Transition
    name="updating-price"
    mode="out-in"
  >
    <span
      v-bind="attrs"
      :key="value"
      class="updating-price"
    >
      {{ value }}
    </span>
  </Transition>
</template>

<script setup lang="ts">
import { useAttrs } from 'vue'

defineOptions({
  inheritAttrs: false,
})

defineProps<{
  value: string
}>()

const attrs = useAttrs()
</script>

<style scoped>
.updating-price {
  display: inline-block;
}

.updating-price-enter-active,
.updating-price-leave-active {
  transition: opacity 160ms ease, transform 160ms ease;
}

.updating-price-enter-from {
  opacity: 0;
  transform: translateY(-0.2rem);
}

.updating-price-leave-to {
  opacity: 0;
  transform: translateY(0.2rem);
}
</style>
