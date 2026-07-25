<template>
  <div class="modal-overlay evidence-review-modal" @click.self="$emit('close')">
    <div class="card modal-content">
      <div class="modal-header"><h3>Review evidence</h3><button type="button" class="modal-close" aria-label="Close" @click="$emit('close')">×</button></div>
      <p><strong>Source excerpt:</strong> {{ item.excerpt }}</p>
      <label>Original value<input :value="item.original_value" readonly></label>
      <p>Current treatment: {{ item.current_treatment.state || 'default' }}</p>
      <label>Fact key <span title="Describe it in one ample term such as `corporate_action` or `earnings_result`.">ⓘ</span><input v-model="form.factKey" list="fact-keys" @blur="normalizeFactKey"></label>
      <datalist id="fact-keys"><option v-for="key in factKeySuggestions" :key="key" :value="key" /></datalist>
      <label>Corrected value<input v-model="form.correctedValue"></label>
      <label>Correction state<select v-model="form.correctionState"><option value="corrected">corrected</option><option value="disputed">disputed</option><option value="stale">stale</option></select></label>
      <label>Artifact review<select v-model="form.artifactReview"><option value="">No artifact review</option><option value="accepted">accepted</option><option value="disputed">disputed</option><option value="stale">stale</option></select></label>
      <label>Reason<input v-model="form.reason"></label>
      <div class="modal-actions"><button type="button" class="btn btn-secondary" @click="$emit('close')">Cancel</button><button type="button" class="btn btn-success" :disabled="!canSave" @click="save">Save</button></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive } from 'vue'
import type { EvidenceReviewItem } from '@/types'

defineProps<{ item: EvidenceReviewItem; factKeySuggestions: string[] }>()
const emit = defineEmits<{ close: []; save: [value: { factKey: string; correctedValue: string; correctionState: 'corrected' | 'disputed' | 'stale'; artifactReview: '' | 'accepted' | 'disputed' | 'stale'; reason: string }] }>()
const form = reactive({ factKey: '', correctedValue: '', correctionState: 'corrected' as const, artifactReview: '' as '' | 'accepted' | 'disputed' | 'stale', reason: '' })
const hasCorrection = computed(() => Boolean(form.factKey || form.correctedValue))
const canSave = computed(() => Boolean(form.reason && ((hasCorrection.value && form.factKey && form.correctedValue) || form.artifactReview)))
function normalizeFactKey() { form.factKey = form.factKey.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '') }
function save() { if (canSave.value) emit('save', { ...form }) }
</script>

<style scoped>
.modal-overlay { position: fixed; inset: 0; z-index: 50; display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,.5); }
.modal-content { width: min(32rem, 92vw); max-height: 90vh; overflow: auto; }
.modal-header, .modal-actions { display: flex; align-items: center; justify-content: space-between; gap: .5rem; }
.modal-close { border: 0; background: transparent; color: var(--text); font-size: 1.5rem; cursor: pointer; }
label { display: grid; gap: .25rem; margin-top: .75rem; }
.modal-actions { justify-content: flex-end; margin-top: 1rem; }
</style>
