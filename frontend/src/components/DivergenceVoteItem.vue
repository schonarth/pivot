<template>
  <div
    class="vote-item"
    ref="root"
    @mouseenter="openTooltip"
    @mouseleave="closeTooltip"
    @focusin="openTooltip"
    @focusout="closeTooltip"
  >
    <button
      type="button"
      class="vote-item-button"
      :class="`vote-item-${tone}`"
      :aria-label="accessibleText"
    >
      <span class="vote-item-label">
        {{ label }}
      </span>
      <span
        class="vote-item-arrow"
        aria-hidden="true"
      >
        {{ arrow }}
      </span>
    </button>

    <Teleport to="body">
      <Transition name="vote-tooltip">
        <div
          v-if="showTooltip"
          class="vote-item-tooltip"
          :style="tooltipStyle"
          role="tooltip"
        >
          <div class="vote-item-tooltip-title">
            {{ accessibleText }}
          </div>
          <div class="vote-item-tooltip-body">
            {{ tooltipMessage }}
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref } from 'vue'

defineProps<{
  label: string
  arrow: '↗' | '↘' | '→'
  tone: 'success' | 'danger' | 'neutral'
  accessibleText: string
  tooltipMessage: string
}>()

const showTooltip = ref(false)
const tooltipStyle = ref<Record<string, string>>({})
const root = ref<HTMLElement | null>(null)
let hoverTimer: number | null = null
let resizeListener: (() => void) | null = null

function openTooltip() {
  if (hoverTimer !== null) {
    window.clearTimeout(hoverTimer)
  }
  hoverTimer = window.setTimeout(() => {
    showTooltip.value = true
    void nextTick(() => {
      positionTooltip()
      if (resizeListener === null) {
        resizeListener = () => positionTooltip()
        window.addEventListener('resize', resizeListener)
        window.addEventListener('scroll', resizeListener, true)
      }
    })
    hoverTimer = null
  }, 90)
}

function closeTooltip() {
  if (hoverTimer !== null) {
    window.clearTimeout(hoverTimer)
    hoverTimer = null
  }
  showTooltip.value = false
  tooltipStyle.value = {}
  if (resizeListener !== null) {
    window.removeEventListener('resize', resizeListener)
    window.removeEventListener('scroll', resizeListener, true)
    resizeListener = null
  }
}

function positionTooltip() {
  const element = root.value?.querySelector('.vote-item-button') as HTMLElement | null
  if (!element) return

  const rect = element.getBoundingClientRect()
  const width = 240
  const gap = 8
  const left = Math.min(
    Math.max(rect.right - width, gap),
    window.innerWidth - width - gap,
  )
  const top = Math.max(gap, Math.min(rect.bottom + gap, window.innerHeight - gap - 96))

  tooltipStyle.value = {
    left: `${Math.round(left)}px`,
    top: `${Math.round(top)}px`,
  }
}

onBeforeUnmount(() => {
  if (hoverTimer !== null) {
    window.clearTimeout(hoverTimer)
  }
  if (resizeListener !== null) {
    window.removeEventListener('resize', resizeListener)
    window.removeEventListener('scroll', resizeListener, true)
  }
})
</script>

<style scoped>
.vote-item {
  position: relative;
  display: inline-flex;
  align-items: center;
  min-width: 0;
}

.vote-item-button {
  appearance: none;
  border: 0;
  background: transparent;
  color: inherit;
  padding: 0;
  margin: 0;
  display: inline-flex;
  align-items: baseline;
  gap: 0.2rem;
  cursor: default;
}

.vote-item-label {
  font-size: 0.62rem;
  line-height: 1;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--panel-muted);
}

.vote-item-arrow {
  font-size: 1rem;
  line-height: 1;
  font-weight: 400;
  font-family: -apple-system, "system-ui", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

.vote-item-success .vote-item-arrow {
  color: #4ade80;
}

.vote-item-danger .vote-item-arrow {
  color: #f87171;
}

.vote-item-neutral .vote-item-arrow {
  color: var(--panel-muted);
}

.vote-item-tooltip {
  position: fixed;
  z-index: 20;
  width: 15rem;
  padding: 0.7rem 0.8rem;
  border-radius: 0.45rem;
  background: rgba(15, 23, 42, 0.96);
  color: #e2e8f0;
  font-size: 0.75rem;
  line-height: 1.35;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.24);
  pointer-events: none;
  white-space: normal;
  text-align: left;
}

.vote-item-tooltip-title {
  margin-bottom: 0.3rem;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #f8fafc;
}

.vote-item-tooltip-body {
  line-height: 1.35;
}

.vote-tooltip-enter-active,
.vote-tooltip-leave-active {
  transition: opacity 0.08s ease, transform 0.08s ease;
}

.vote-tooltip-enter-from,
.vote-tooltip-leave-to {
  opacity: 0;
  transform: translateY(-2px);
}
</style>
