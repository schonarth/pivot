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
        v-else-if="resolvedInsight"
        :recommendation="resolvedInsight.recommendation"
        :confidence="resolvedInsight.confidence"
        :summary-text="resolvedInsight.summary"
        :technical-text="resolvedInsight.technical_summary"
        :trajectory-items="resolvedInsight.sentiment_trajectory?.entries ?? []"
        :divergence-analysis="resolvedInsight.divergence_analysis"
        :divergence-summary="resolvedInsight.divergence_summary"
        :divergence-disclosure="resolvedInsight.divergence_disclosure"
        footer-label="News digest"
        :footer-text="resolvedInsight.news_context"
        :model-used="resolvedInsight.model_used"
        :generated-at="resolvedInsight.generated_at"
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
import { onMounted, ref, watch } from 'vue'
import AIInsightNarrative from './AIInsightNarrative.vue'
import { hasExpandedScopeInsight, markExpandedScopeInsight } from './scopeInsightMemory'
import type { MonitoredScopeInsight } from '@/types'

const props = defineProps<{
  title: string
  scopeLabel: string
  assetCount: number
  emptyMessage: string
  insight: MonitoredScopeInsight | null
  loadInsight?: () => Promise<MonitoredScopeInsight | null>
  refreshKey?: string
}>()

const isExpanded = ref(hasExpandedScopeInsight(props.title, props.scopeLabel))
const isLoading = ref(false)
const resolvedInsight = ref<MonitoredScopeInsight | null>(props.insight)
const hasLoaded = ref(Boolean(props.insight))
const pendingRefresh = ref(false)

watch(
  () => props.insight,
  (value) => {
    resolvedInsight.value = value
    hasLoaded.value = Boolean(value)
  },
)

watch(
  () => props.refreshKey,
  () => {
    if (!isExpanded.value || !props.loadInsight) return
    if (isLoading.value) {
      pendingRefresh.value = true
      return
    }
    if (hasLoaded.value) {
      isLoading.value = true
      void loadInsight()
    }
  },
)

function toggleExpanded() {
  isExpanded.value = !isExpanded.value

  if (isExpanded.value) {
    markExpandedScopeInsight(props.title, props.scopeLabel)
  }

  if (isExpanded.value && !hasLoaded.value) {
    if (props.loadInsight) {
      isLoading.value = true
      void loadInsight()
    } else {
      hasLoaded.value = true
    }
  }
}

async function loadInsight() {
  const refreshKeyAtStart = props.refreshKey
  try {
    resolvedInsight.value = await props.loadInsight?.() ?? null
  } finally {
    hasLoaded.value = true
    isLoading.value = false
    if (pendingRefresh.value && isExpanded.value && props.refreshKey !== refreshKeyAtStart) {
      pendingRefresh.value = false
      isLoading.value = true
      void loadInsight()
      return
    }
    pendingRefresh.value = false
  }
}

onMounted(() => {
  if (isExpanded.value && !hasLoaded.value && props.loadInsight) {
    isLoading.value = true
    void loadInsight()
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
