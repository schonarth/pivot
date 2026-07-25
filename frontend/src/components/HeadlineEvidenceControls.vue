<template>
  <span v-if="item">
    <EvidenceArtifactControls :item="item" @review="openReview" @stance="setStance" />
    <EvidenceReviewModal v-if="isOpen" :item="item" :fact-key-suggestions="suggestions" @close="closeReview" @save="save" />
  </span>
</template>

<script lang="ts">
import { ref } from 'vue'

const activeNewsItemId = ref<string | null>(null)
</script>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { clearSourceStance, createArtifactReview, createFactCorrection, getNewsItemEvidence, setSourceStance } from '@/api/ai'
import type { EvidenceReviewItem } from '@/types'
import EvidenceArtifactControls from './EvidenceArtifactControls.vue'
import EvidenceReviewModal from './EvidenceReviewModal.vue'

const props = defineProps<{ newsItemId?: string }>()
const item = ref<EvidenceReviewItem | null>(null)
const suggestions = ref<string[]>([])
const isOpen = computed(() => activeNewsItemId.value === props.newsItemId)

function openReview() {
  activeNewsItemId.value = props.newsItemId || null
}

function closeReview() {
  if (isOpen.value) activeNewsItemId.value = null
}

async function load() {
  if (!props.newsItemId) return
  const review = await getNewsItemEvidence(props.newsItemId)
  item.value = review.evidence[0] || null
  suggestions.value = review.fact_key_suggestions
}
async function save(value: { factKey: string; correctedValue: string; correctionState: 'corrected' | 'disputed' | 'stale'; artifactReview: '' | 'accepted' | 'disputed' | 'stale'; reason: string }) {
  if (!item.value) return
  if (value.factKey && value.correctedValue) await createFactCorrection({ news_item_id: item.value.news_item_id, fact_key: value.factKey, corrected_value: value.correctedValue, correction_state: value.correctionState, reason: value.reason })
  if (value.artifactReview) await createArtifactReview({ news_item_id: item.value.news_item_id, artifact_review_state: value.artifactReview, reason: value.reason })
  closeReview()
  await load()
}
async function setStance(stance: 'trusted' | 'untrusted' | null) {
  if (!item.value) return
  if (stance) await setSourceStance(item.value.source_id, stance)
  else await clearSourceStance(item.value.source_id)
  await load()
}
onMounted(load)
</script>
