<template>
  <span class="badge badge-info" v-if="preferredBadge === 'both'">
    {{props.market}}
    <div class="market-flag">{{ marketFlag }}</div>
  </span>
  <span v-else-if="preferredBadge === 'flag'">
    <div class="market-flag">{{ marketFlag }}</div>
  </span>
  <span class="badge badge-info" v-else>
    {{props.market}}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSettingsStore } from '@/stores/settings'

type Market = 'BR' | 'EU' | 'US' | 'UK' | string

const flags: Record<Market, string> = {
  'BR': '🇧🇷',
  'EU': '🇪🇺',
  'US': '🇺🇸',
  'UK': '🇬🇧',
}

const props = defineProps<{
  market: Market
}>()

const settings = useSettingsStore()
const preferredBadge = computed(() => settings.marketBadgeStyle)

const marketFlag = computed(() => flags[props.market] || props.market)
</script>

<style scoped>
.market-flag {
  font-size: 1.5rem;
  margin-left: 4px;
}
</style>
