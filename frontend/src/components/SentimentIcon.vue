<template>
  <div
    class="sentiment-icon"
    ref="root"
    @mouseenter="openTooltip"
    @mouseleave="closeTooltip"
    @focusin="openTooltip"
    @focusout="closeTooltip"
  >
    <button
      type="button"
      class="sentiment-icon-button"
      :class="[`sentiment-icon-${state}`, `sentiment-icon-button-${state}`]"
      :aria-label="`${symbol}: ${tooltipMessage}`"
    >
      <span
        class="sentiment-icon-glyph"
        aria-hidden="true"
      >
        {{ sentimentGlyph }}
      </span>
      <span class="sentiment-icon-symbol">
        {{ symbol }}
      </span>
    </button>

    <Teleport to="body">
      <Transition name="sentiment-tooltip">
        <div
          v-if="showTooltip"
          class="sentiment-icon-tooltip"
          :class="`sentiment-icon-tooltip-${state}`"
          :style="tooltipStyle"
          role="tooltip"
        >
          <div class="sentiment-icon-tooltip-title">
            {{ tooltipTitle }}
          </div>
          <div class="sentiment-icon-tooltip-body">
            <strong>{{ symbol }}</strong>
            <span>{{ tooltipMessage }}</span>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, nextTick } from 'vue'

const props = defineProps<{
  state: 'improving' | 'deteriorating' | 'conflicting' | 'reversal'
  symbol: string
  tooltipTitle: string
  tooltipMessage: string
}>()

const showTooltip = ref(false)
const tooltipStyle = ref<Record<string, string>>({})
const root = ref<HTMLElement | null>(null)
let hoverTimer: number | null = null
let resizeListener: (() => void) | null = null

const sentimentGlyph = computed(() => {
  if (props.state === 'improving') return '📈'
  if (props.state === 'deteriorating') return '📉'
  if (props.state === 'reversal') return '🔀'
  return '💢'
})

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
  const element = root.value?.querySelector('.sentiment-icon-button') as HTMLElement | null
  if (!element) return

  const rect = element.getBoundingClientRect()
  const width = 224
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
.sentiment-icon {
  position: relative;
  display: inline-flex;
  flex-direction: column;
  align-items: center;
}

.sentiment-icon-button {
  appearance: none;
  border: 0;
  background: transparent;
  color: inherit;
  padding: 0.05rem 0.15rem;
  margin: 0;
  width: 3.9rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.15rem;
  cursor: default;
}

.sentiment-icon-glyph {
  font-size: 1.7rem;
  line-height: 1;
}

.sentiment-icon-symbol {
  font-size: 0.68rem;
  line-height: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
  text-align: center;
}

.sentiment-icon-tooltip {
  position: fixed;
  z-index: 20;
  width: 14rem;
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

.sentiment-icon-tooltip-title {
  margin-bottom: 0.3rem;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #f8fafc;
}

.sentiment-icon-tooltip-improving .sentiment-icon-tooltip-title {
  color: #86efac;
}

.sentiment-icon-tooltip-deteriorating .sentiment-icon-tooltip-title {
  color: #fca5a5;
}

.sentiment-icon-tooltip-reversal .sentiment-icon-tooltip-title {
  color: #fcd34d;
}

.sentiment-icon-tooltip-conflicting .sentiment-icon-tooltip-title {
  color: #c4b5fd;
}

.sentiment-icon-tooltip-body {
  line-height: 1.35;
}

.sentiment-icon-tooltip-body strong {
  font-weight: 700;
  margin-right: 0.25rem;
  color: #ffffff;
}

.sentiment-tooltip-enter-active,
.sentiment-tooltip-leave-active {
  transition: opacity 0.08s ease, transform 0.08s ease;
}

.sentiment-tooltip-enter-from,
.sentiment-tooltip-leave-to {
  opacity: 0;
  transform: translateY(-2px);
}

.sentiment-icon-improving {
  transform: translateY(-1px);
}

.sentiment-icon-button-improving .sentiment-icon-glyph {
  color: #4ade80;
}

.sentiment-icon-deteriorating {
  transform: translateY(-1px);
}

.sentiment-icon-button-deteriorating .sentiment-icon-glyph {
  color: #f87171;
}

.sentiment-icon-reversal {
  transform: translateY(-1px);
}

.sentiment-icon-button-reversal .sentiment-icon-glyph {
  color: #f59e0b;
}

.sentiment-icon-conflicting {
  transform: translateY(-1px);
}

.sentiment-icon-button-conflicting .sentiment-icon-glyph {
  color: #a78bfa;
}
</style>
