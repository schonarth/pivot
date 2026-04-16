<template>
  <div class="card">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem;">
      <div>
        <h3 style="margin-bottom: 0.25rem;">
          {{ title }}
        </h3>
        <div class="text-muted" style="font-size: 0.75rem;">
          {{ scopeLabel }} · {{ assetCount }} assets
        </div>
      </div>
      <span class="badge badge-secondary">
        AI Summary
      </span>
    </div>

    <div
      v-if="insight"
      style="margin-top: 1rem;"
    >
      <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center;">
        <span class="badge badge-info">
          {{ insight.recommendation }}
        </span>
        <span class="badge badge-secondary">
          {{ insight.confidence }}% confidence
        </span>
      </div>

      <p style="margin: 0.9rem 0 0; line-height: 1.6;">
        {{ insight.summary }}
      </p>

      <div
        v-if="insight.technical_summary"
        class="text-muted"
        style="margin-top: 0.75rem; font-size: 0.85rem; line-height: 1.5;"
      >
        {{ insight.technical_summary }}
      </div>

      <div
        v-if="insight.news_context"
        class="text-muted"
        style="margin-top: 0.5rem; font-size: 0.85rem; line-height: 1.5;"
      >
        {{ insight.news_context }}
      </div>

      <div
        class="text-muted"
        style="margin-top: 0.75rem; font-size: 0.7rem;"
      >
        {{ formatDate(insight.generated_at) }} · {{ insight.model_used }}
      </div>
    </div>

    <div
      v-else
      class="text-muted"
      style="margin-top: 1rem;"
    >
      {{ emptyMessage }}
    </div>
  </div>
</template>

<script setup lang="ts">
import type { MonitoredScopeInsight } from '@/types'

defineProps<{
  title: string
  scopeLabel: string
  assetCount: number
  emptyMessage: string
  insight: MonitoredScopeInsight | null
}>()

function formatDate(value: string): string {
  return new Date(value).toLocaleString()
}
</script>
