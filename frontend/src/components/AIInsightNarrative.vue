<template>
  <div class="insight-narrative">
    <div
      v-if="trajectoryItems.length"
      class="trajectory-strip"
    >
      <div class="trajectory-grid">
        <SentimentIcon
          v-for="item in trajectoryItems"
          :key="`${item.subject_type}-${item.subject}`"
          :state="item.state"
          :symbol="item.subject"
          :tooltip-title="trajectoryTitle(item.state)"
          :tooltip-message="trajectoryTooltip(item)"
        />
      </div>
    </div>

    <div class="insight-content">
      <div style="display: flex; gap: 0.75rem; flex-wrap: wrap; margin-bottom: 1rem;">
        <span
          class="badge"
          :class="recommendationBadgeClass(recommendation)"
        >
          {{ recommendation }}
        </span>
        <span class="badge badge-secondary">
          Confidence {{ confidence }}%
        </span>
        <span
          v-if="priceTarget != null"
          class="badge badge-secondary"
        >
          Target {{ priceTarget }}
        </span>
      </div>

      <p
        v-if="summaryText"
        style="margin-bottom: 0.75rem; line-height: 1.6;"
      >
        {{ summaryText }}
      </p>

      <p
        v-if="technicalText"
        class="text-muted"
        style="margin-bottom: 0.75rem; font-size: 0.85rem; line-height: 1.5;"
      >
        {{ technicalText }}
      </p>

      <div v-if="footerText">
        <div
          class="text-muted"
          style="font-size: 0.75rem; margin-bottom: 0.35rem;"
        >
          {{ footerLabel }}
        </div>
        <p
          class="text-muted"
          style="margin: 0; font-size: 0.85rem; line-height: 1.5;"
        >
          {{ footerText }}
        </p>
      </div>

      <div v-else-if="footnotes.length">
        <div
          class="text-muted"
          style="font-size: 0.75rem; margin-bottom: 0.35rem;"
        >
          {{ footerLabel }}
        </div>
        <ul style="margin: 0; padding-left: 1rem;">
          <li
            v-for="item in footnotes"
            :key="`${item.source}-${item.headline}`"
            class="text-muted"
            style="margin-bottom: 0.35rem; font-size: 0.85rem; line-height: 1.5;"
          >
            <a
              v-if="item.url"
              :href="item.url"
              target="_blank"
              rel="noopener noreferrer"
              style="color: inherit; text-decoration: underline;"
            >
              {{ item.headline }}
            </a>
            <span v-else>
              {{ item.headline }}
            </span>
            <span class="text-muted">({{ item.source }})</span>
          </li>
        </ul>
      </div>

      <div
        v-if="modelUsed || generatedAt"
        class="text-muted"
        style="margin-top: 0.75rem; font-size: 0.7rem;"
      >
        <span v-if="generatedAt">{{ formatDate(generatedAt) }}</span>
        <span v-if="modelUsed">
          <template v-if="generatedAt"> · </template>{{ modelUsed }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import SentimentIcon from './SentimentIcon.vue'

type FootnoteItem = {
  headline: string
  url?: string
  source: string
}

type TrajectoryItem = {
  subject_type: 'asset' | 'theme'
  subject: string
  state: 'improving' | 'deteriorating' | 'conflicting' | 'reversal'
  summary: string
  evidence_count: number
}

const props = defineProps<{
  recommendation: 'BUY' | 'HOLD' | 'SELL'
  confidence: number
  summaryText: string
  technicalText?: string
  trajectoryItems?: TrajectoryItem[]
  footerLabel: string
  footerText?: string
  footnotes?: FootnoteItem[]
  priceTarget?: number | null
  modelUsed?: string
  generatedAt?: string
}>()

const footnotes = computed(() => props.footnotes ?? [])
const trajectoryItems = computed(() => props.trajectoryItems ?? [])

function recommendationBadgeClass(recommendation: string): string {
  if (recommendation === 'BUY') return 'badge-success'
  if (recommendation === 'SELL') return 'badge-danger'
  return 'badge-warning'
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString()
}

function trajectoryTooltip(item: TrajectoryItem): string {
  return item.summary
    .replace(/^Asset\s+[A-Z0-9.\-]+\s+/i, '')
    .replace(/^Theme\s+/i, '')
    .replace(/\b(retained items?|headlines?)\b/i, 'headlines')
}

function trajectoryTitle(state: TrajectoryItem['state']): string {
  if (state === 'improving') return 'Improved'
  if (state === 'deteriorating') return 'Deteriorated'
  if (state === 'reversal') return 'Flipped'
  return 'Conflicted'
}
</script>

<style scoped>
.trajectory-strip {
  position: absolute;
  top: 0;
  right: 0;
  max-width: 10rem;
}

.trajectory-grid {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.4rem;
  max-width: 100%;
}

.insight-narrative {
  position: relative;
  padding-top: 0.15rem;
  padding-right: 10.5rem;
}

.insight-content {
  min-width: 0;
}

@media (max-width: 720px) {
  .insight-narrative {
    padding-right: 0;
  }

  .trajectory-strip {
    position: static;
    max-width: none;
    margin: 0 0 0.9rem;
  }
}
</style>
