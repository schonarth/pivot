<template>
  <div class="card">
    <button
      class="scope-insight-header"
      type="button"
      @click="toggleExpanded"
    >
      <div>
        <h3 style="margin-bottom: 0.25rem;">
          {{ title }}
        </h3>
        <div class="text-muted" style="font-size: 0.75rem;">
          {{ scopeLabel }} · {{ assetCount }} assets
        </div>
      </div>
      <div style="display: flex; align-items: center; gap: 0.5rem;">
        <span class="badge badge-secondary">
          AI Summary
        </span>
        <span
          class="scope-insight-chevron"
          :class="{ open: isExpanded }"
          aria-hidden="true"
        >
          ›
        </span>
      </div>
    </button>

    <div
      v-if="isExpanded"
      style="margin-top: 1rem;"
    >
      <div
        v-if="isLoading"
        class="scope-insight-loading"
      >
        <span class="spinner" />
      </div>
      <AIInsightNarrative
        v-else-if="insight"
        :recommendation="insight.recommendation"
        :confidence="insight.confidence"
        :summary-text="insight.summary"
        :technical-text="insight.technical_summary"
        :trajectory-items="insight.sentiment_trajectory?.entries ?? []"
        footer-label="News digest"
        :footer-text="insight.news_context"
        :model-used="insight.model_used"
        :generated-at="insight.generated_at"
      />
      <div
        v-else
        class="text-muted"
      >
        {{ emptyMessage }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'
import AIInsightNarrative from './AIInsightNarrative.vue'
import { hasExpandedScopeInsight, markExpandedScopeInsight } from './scopeInsightMemory'
import type { MonitoredScopeInsight } from '@/types'

const props = defineProps<{
  title: string
  scopeLabel: string
  assetCount: number
  emptyMessage: string
  insight: MonitoredScopeInsight | null
}>()

const isExpanded = ref(hasExpandedScopeInsight(props.title, props.scopeLabel))
const isLoading = ref(false)
const hasLoaded = ref(isExpanded.value)
let loadTimer: number | null = null

function toggleExpanded() {
  isExpanded.value = !isExpanded.value

  if (isExpanded.value && !hasLoaded.value) {
    markExpandedScopeInsight(props.title, props.scopeLabel)
    isLoading.value = true
    if (loadTimer !== null) {
      window.clearTimeout(loadTimer)
    }
    loadTimer = window.setTimeout(() => {
      hasLoaded.value = true
      isLoading.value = false
      loadTimer = null
    }, 0)
  }
}

onBeforeUnmount(() => {
  if (loadTimer !== null) {
    window.clearTimeout(loadTimer)
  }
})
</script>

<style scoped>
.scope-insight-header {
  width: 100%;
  border: 0;
  background: transparent;
  color: inherit;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  padding: 0;
  cursor: pointer;
  text-align: left;
}

.scope-insight-chevron {
  color: var(--text-muted);
  font-size: 1.5rem;
  line-height: 1;
  transition: transform 0.15s ease;
  transform: rotate(90deg);
}

.scope-insight-chevron.open {
  transform: rotate(-90deg);
}

.scope-insight-loading {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
