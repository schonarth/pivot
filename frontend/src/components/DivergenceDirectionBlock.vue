<template>
  <div
    class="direction-block"
    :class="[`direction-block-${tone}`, { 'direction-block-emphasis': emphasis }]"
  >
    <span class="direction-kicker">
      {{ label }}
    </span>
    <strong>{{ value }}</strong>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  label: string
  value: string
  tone: 'neutral' | 'success' | 'warning' | 'danger'
  emphasis?: boolean
}>()
</script>

<style scoped>
.direction-block {
  min-height: 4rem;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.direction-kicker {
  font-size: 0.65rem;
  line-height: 1;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--panel-muted);
  margin-bottom: 0.12rem;
}

.direction-block strong {
  font-size: 1.45rem;
  line-height: .5;
  letter-spacing: -0.04em;
  color: var(--text-primary);
  text-transform: lowercase;
}

.direction-block-emphasis strong {
  font-size: 1.7rem;
  margin-top: -0.04rem;
}

.direction-block-success strong {
  color: #86efac;
}

.direction-block-warning strong {
  color: #fbbf24;
}

.direction-block-danger strong {
  color: #fca5a5;
}

.direction-block-neutral strong {
  color: var(--panel-muted);
}
</style>
