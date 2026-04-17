<template>
  <div>
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
</template>

<script setup lang="ts">
import { computed } from 'vue'

type FootnoteItem = {
  headline: string
  url?: string
  source: string
}

const props = defineProps<{
  recommendation: 'BUY' | 'HOLD' | 'SELL'
  confidence: number
  summaryText: string
  technicalText?: string
  footerLabel: string
  footerText?: string
  footnotes?: FootnoteItem[]
  priceTarget?: number | null
  modelUsed?: string
  generatedAt?: string
}>()

const footnotes = computed(() => props.footnotes ?? [])

function recommendationBadgeClass(recommendation: string): string {
  if (recommendation === 'BUY') return 'badge-success'
  if (recommendation === 'SELL') return 'badge-danger'
  return 'badge-warning'
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString()
}
</script>
