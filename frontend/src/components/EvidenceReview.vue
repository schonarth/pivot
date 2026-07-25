<template>
  <section class="evidence-review">
    <h3>Evidence review</h3>
    <p v-if="loading">Loading evidence…</p>
    <p v-else-if="!review?.evidence.length">No cited evidence.</p>
    <div v-for="item in review?.evidence" :key="item.news_item_id" class="evidence-item">
      <div class="evidence-item-header">
        <div><strong>{{ item.excerpt }}</strong><span class="text-muted"> · {{ item.source_name }}</span></div>
        <EvidenceArtifactControls :item="item" @review="activeItem = item" @stance="setStance(item, $event)" />
      </div>
      <p v-if="item.categorical_uncertainty">Uncertainty: {{ item.categorical_uncertainty }}</p>
      <ul v-if="item.correction_history.length || item.artifact_review_history.length" class="evidence-history">
        <li v-for="correction in item.correction_history" :key="correction.id">{{ correction.fact_key }}: {{ correction.corrected_value }} ({{ correction.correction_state }})</li>
        <li v-for="artifactReview in item.artifact_review_history" :key="artifactReview.id">{{ artifactReview.artifact_review_state }}: {{ artifactReview.reason }}</li>
      </ul>
    </div>
    <EvidenceReviewModal v-if="activeItem" :item="activeItem" :fact-key-suggestions="review?.fact_key_suggestions || []" @close="activeItem = null" @save="save" />
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { clearSourceStance, createArtifactReview, createFactCorrection, getRecommendationEvidence, setSourceStance } from '@/api/ai'
import type { EvidenceReviewItem, EvidenceReviewResponse } from '@/types'
import EvidenceArtifactControls from './EvidenceArtifactControls.vue'
import EvidenceReviewModal from './EvidenceReviewModal.vue'

const props = defineProps<{ recommendationId: string; enableSourceStanceControls?: boolean }>()
const review = ref<EvidenceReviewResponse | null>(null)
const activeItem = ref<EvidenceReviewItem | null>(null)
const loading = ref(true)
async function load() {
  loading.value = true
  try { review.value = await getRecommendationEvidence(props.recommendationId, props.enableSourceStanceControls) } finally { loading.value = false }
}
async function save(value: { factKey: string; correctedValue: string; correctionState: 'corrected' | 'disputed' | 'stale'; artifactReview: '' | 'accepted' | 'disputed' | 'stale'; reason: string }) {
  if (!activeItem.value) return
  if (value.factKey && value.correctedValue) await createFactCorrection({ news_item_id: activeItem.value.news_item_id, fact_key: value.factKey, corrected_value: value.correctedValue, correction_state: value.correctionState, reason: value.reason })
  if (value.artifactReview) await createArtifactReview({ news_item_id: activeItem.value.news_item_id, artifact_review_state: value.artifactReview, reason: value.reason })
  activeItem.value = null
  await load()
}
async function setStance(item: EvidenceReviewItem, stance: 'trusted' | 'untrusted' | null) {
  if (stance) await setSourceStance(item.source_id, stance)
  else await clearSourceStance(item.source_id)
  await load()
}
onMounted(load)
</script>

<style scoped>
.evidence-review { border-top: 1px solid var(--border); margin-top: .875rem; padding-top: .75rem; }
.evidence-item { border-top: 1px solid var(--border); margin-top: .75rem; padding-top: .75rem; }
.evidence-item-header { display: flex; align-items: center; justify-content: space-between; gap: .75rem; }
.evidence-history { margin: .5rem 0; padding-left: 1rem; }
</style>
