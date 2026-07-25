<template>
  <div ref="controls" class="evidence-artifact-controls">
    <button class="evidence-review-trigger" type="button" @click="$emit('review')">
      Review
    </button>
    <div class="source-stance-menu">
      <button
        class="source-stance-trigger"
        type="button"
        :disabled="!item.source_stance_controls_enabled"
        @click="open = !open"
      >
        {{ triggerLabel }} <span aria-hidden="true">⌄</span>
      </button>
      <div v-if="open" class="source-stance-options">
        <button v-for="option in options" :key="option.value || 'clear'" type="button" @click="select(option.value)">
          {{ option.label }}
        </button>
      </div>
    </div>
    <small v-if="!item.source_stance_controls_enabled" class="source-stance-help">Source stance requires at least two eligible configured sources.</small>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import type { EvidenceReviewItem } from '@/types'

const props = defineProps<{ item: EvidenceReviewItem }>()
const emit = defineEmits<{ review: []; stance: [value: 'trusted' | 'untrusted' | null] }>()
const open = ref(false)
const controls = ref<HTMLElement | null>(null)

const triggerLabel = computed(() => {
  if (props.item.source_stance === 'trusted') return 'Trusted source'
  if (props.item.source_stance === 'untrusted') return 'Untrusted source'
  return 'Trust source'
})
const options = computed(() => {
  if (props.item.source_stance === 'trusted') return [{ value: null, label: 'Clear' }, { value: 'untrusted' as const, label: 'Do not trust' }]
  if (props.item.source_stance === 'untrusted') return [{ value: null, label: 'Clear' }, { value: 'trusted' as const, label: 'Trust source' }]
  return [{ value: 'trusted' as const, label: 'Trust source' }, { value: 'untrusted' as const, label: 'Do not trust' }]
})
function select(value: 'trusted' | 'untrusted' | null) {
  open.value = false
  emit('stance', value)
}

function closeOutside(event: MouseEvent) {
  if (!controls.value?.contains(event.target as Node)) open.value = false
}

onMounted(() => document.addEventListener('click', closeOutside))
onBeforeUnmount(() => document.removeEventListener('click', closeOutside))
</script>

<style scoped>
.evidence-artifact-controls { display: inline-flex; flex: 0 0 auto; align-items: center; gap: .375rem; margin-left: .375rem; white-space: nowrap; }
.evidence-review-trigger, .source-stance-trigger { border: 0; background: transparent; color: #fff; cursor: pointer; font-weight: 700; padding: 0; white-space: nowrap; }
.evidence-review-trigger:hover, .source-stance-trigger:hover { text-decoration: underline; }
.source-stance-trigger:disabled { cursor: not-allowed; opacity: .55; text-decoration: none; }
.source-stance-menu { position: relative; flex: 0 0 auto; }
.source-stance-trigger { display: inline-flex; align-items: center; gap: .15rem; }
.source-stance-options { position: absolute; z-index: 4; right: 0; top: calc(100% + .25rem); min-width: 8rem; padding: .25rem; border: 1px solid var(--border); border-radius: .375rem; background: var(--card-bg); box-shadow: 0 .5rem 1rem rgba(0, 0, 0, .16); }
.source-stance-options button { display: block; width: 100%; border: 0; background: transparent; color: #fff; padding: .375rem .5rem; text-align: left; cursor: pointer; }
.source-stance-options button:hover { background: var(--hover-bg); }
</style>
