<template>
  <div class="insight-narrative">
    <div class="insight-content">
      <div class="insight-badges">
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
        class="insight-summary"
      >
        {{ summaryText }}
      </p>

      <p
        v-if="technicalText"
        class="insight-technical text-muted"
      >
        {{ technicalText }}
      </p>

      <div v-if="footerText">
        <div class="section-label">
          {{ footerLabel }}
        </div>
        <p class="footer-text text-muted">
          {{ footerText }}
        </p>
      </div>

      <div v-else-if="footnotes.length">
        <div class="section-label">
          {{ footerLabel }}
        </div>
        <ul class="footnote-list">
          <li
            v-for="item in footnotes"
            :key="`${item.source}-${item.headline}`"
            class="text-muted"
          >
            <a
              v-if="item.url"
              :href="item.url"
              target="_blank"
              rel="noopener noreferrer"
              class="footnote-link"
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

    <aside class="insight-rail">
      <div
        v-if="trajectoryItems.length"
        class="trajectory-strip"
      >
        <div class="section-label">
          Sentiment trajectory
        </div>
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

      <div
        v-if="divergenceAnalysis"
        class="divergence-infographic"
        :class="`tone-${divergenceTone}`"
      >
        <div class="divergence-infographic__glow" />
        <div class="divergence-infographic__header">
          <div>
            <div class="section-label">
              Divergence
            </div>
            <div class="divergence-title">
              {{ divergenceHeadline }}
            </div>
          </div>
          <span
            class="divergence-seal"
            :class="divergenceSealClass"
          >
            {{ divergenceSeal }}
          </span>
        </div>

        <div class="divergence-diagram">
          <DivergenceDirectionBlock
            label="Expected"
            :value="divergenceAnalysis.expected_direction"
            :tone="directionTone(divergenceAnalysis.expected_direction)"
          />
          <div class="diagram-center">
            <div
              class="diagram-percent"
              title="Move size"
              aria-label="Move size"
            >
              <span class="diagram-percent-value">
                {{ formatMove(divergenceAnalysis.actual_percent_move) }}
              </span>
            </div>
            <div
              class="diagram-arrow"
              :title="divergenceArrowLabel"
              :aria-label="divergenceArrowLabel"
              role="img"
            >
              {{ divergenceArrow }}
            </div>
          </div>
          <DivergenceDirectionBlock
            label="Actual"
            :value="divergenceAnalysis.actual_direction"
            :tone="directionTone(divergenceAnalysis.actual_direction)"
            emphasis
          />
        </div>

        <p class="divergence-copy">
          {{ divergenceSummaryText }}
        </p>

        <div class="divergence-votes">
          <DivergenceVoteItem
            v-for="vote in divergenceVotes"
            :key="vote.label"
            :label="vote.label"
            :arrow="vote.arrow"
            :tone="vote.tone"
            :accessible-text="`${vote.label}: ${vote.value}`"
            :tooltip-message="vote.tooltipMessage"
          />
        </div>

        <p class="divergence-note">
          {{ divergenceDisclosureText }}
        </p>
      </div>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { DivergenceAnalysis } from '@/types'
import DivergenceDirectionBlock from './DivergenceDirectionBlock.vue'
import DivergenceVoteItem from './DivergenceVoteItem.vue'
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
  divergenceAnalysis?: DivergenceAnalysis | null
  divergenceSummary?: string
  divergenceDisclosure?: string
  footerLabel: string
  footerText?: string
  footnotes?: FootnoteItem[]
  priceTarget?: number | null
  modelUsed?: string
  generatedAt?: string
}>()

const footnotes = computed(() => props.footnotes ?? [])
const trajectoryItems = computed(() => props.trajectoryItems ?? [])
const divergenceSummaryText = computed(() => props.divergenceSummary ?? buildDivergenceSummary(props.divergenceAnalysis))
const divergenceDisclosureText = computed(() => props.divergenceDisclosure ?? 'Short-window divergence is informational only and does not drive trades.')
const divergenceTone = computed(() => getDivergenceTone(props.divergenceAnalysis))
const divergenceHeadline = computed(() => getDivergenceHeadline(props.divergenceAnalysis))
const divergenceSeal = computed(() => getDivergenceSeal(props.divergenceAnalysis))
const divergenceSealClass = computed(() => getDivergenceSealClass(props.divergenceAnalysis))
const divergenceArrow = computed(() => getDivergenceArrow(props.divergenceAnalysis))
const divergenceArrowLabel = computed(() => getDivergenceArrowLabel(props.divergenceAnalysis))
const divergenceVotes = computed(() => buildDivergenceVotes(props.divergenceAnalysis))
const divergenceVoteCopy = {
  Technical: 'Built from price action and indicator alignment in the asset itself, Technical pulls from the chart, momentum, and trend signals, and it helps set the base directional expectation.',
  Context: 'Built from asset-specific news and sentiment, Context reflects how recent headlines and item-level context are leaning, and it can override a purely chart-based read when the story points elsewhere.',
  Trajectory: 'Built from the short-window sentiment trajectory for the asset, Trajectory measures whether recent sentiment is improving, deteriorating, or turning, and it nudges the output when that drift is consistent.',
  Shared: 'Built from broader sector, theme, or macro context around the monitored set, Shared matters most when the wider backdrop confirms or conflicts with the asset-level read, especially for portfolio and watchlist views.',
} as const

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

function formatMove(value: string): string {
  const numeric = Number.parseFloat(value)
  if (!Number.isFinite(numeric)) return '0.00%'
  return `${(numeric * 100).toFixed(2)}%`
}

function getDivergenceTone(divergenceAnalysis?: DivergenceAnalysis | null): 'success' | 'warning' | 'danger' | 'neutral' {
  if (!divergenceAnalysis) return 'neutral'
  if (divergenceAnalysis.label === 'no_divergence') return 'success'
  if (divergenceAnalysis.label === 'no_material_follow_through') return 'warning'
  if (divergenceAnalysis.label === 'competing_macro_priority') return 'danger'
  if (divergenceAnalysis.label === 'reversal') return 'danger'
  if (divergenceAnalysis.label === 'uncertainty_conflict') return 'warning'
  return 'neutral'
}

function getDivergenceHeadline(divergenceAnalysis?: DivergenceAnalysis | null): string {
  if (!divergenceAnalysis) return 'Divergence'
  if (divergenceAnalysis.label === 'no_divergence') return 'Nailed it'
  if (divergenceAnalysis.label === 'no_material_follow_through') return 'Signal faded'
  if (divergenceAnalysis.label === 'competing_macro_priority') return 'Macro won'
  if (divergenceAnalysis.label === 'reversal') return 'Price reversed'
  if (divergenceAnalysis.label === 'uncertainty_conflict') return 'No clean read'
  if (divergenceAnalysis.label === 'insufficient_signal') return 'No read'
  return 'Divergence'
}

function getDivergenceSeal(divergenceAnalysis?: DivergenceAnalysis | null): string {
  if (divergenceAnalysis?.label === 'no_divergence') return 'MATCH'
  return 'NO MATCH'
}

function getDivergenceSealClass(divergenceAnalysis?: DivergenceAnalysis | null): string {
  if (divergenceAnalysis?.label === 'no_divergence') return 'seal-match'
  return 'seal-no-match'
}

function getDivergenceArrow(divergenceAnalysis?: DivergenceAnalysis | null): string {
  if (!divergenceAnalysis) return '→'
  if (divergenceAnalysis.label === 'no_divergence') return '='
  if (divergenceAnalysis.label === 'no_material_follow_through') return '↔'
  if (divergenceAnalysis.label === 'competing_macro_priority') return '↘'
  if (divergenceAnalysis.label === 'reversal') return '↩'
  if (divergenceAnalysis.label === 'uncertainty_conflict') return '≈'
  return '→'
}

function getDivergenceArrowLabel(divergenceAnalysis?: DivergenceAnalysis | null): string {
  if (!divergenceAnalysis) return 'neutral'
  if (divergenceAnalysis.label === 'no_divergence') return 'match'
  if (divergenceAnalysis.label === 'no_material_follow_through') return 'flat'
  if (divergenceAnalysis.label === 'competing_macro_priority') return 'down'
  if (divergenceAnalysis.label === 'reversal') return 'reversal'
  if (divergenceAnalysis.label === 'uncertainty_conflict') return 'approximate'
  return 'neutral'
}

function buildDivergenceSummary(divergenceAnalysis?: DivergenceAnalysis | null): string {
  if (!divergenceAnalysis) return ''
  if (divergenceAnalysis.label === 'no_divergence') {
    return `Nailed it. Expected ${divergenceAnalysis.expected_direction}, and the move matched.`
  }
  if (divergenceAnalysis.label === 'no_material_follow_through') {
    return `Expected ${divergenceAnalysis.expected_direction}, but the move stayed flat.`
  }
  if (divergenceAnalysis.label === 'competing_macro_priority') {
    return `Expected ${divergenceAnalysis.expected_direction}, but broader context matched the opposite move.`
  }
  if (divergenceAnalysis.label === 'reversal') {
    return `Expected ${divergenceAnalysis.expected_direction}, but the move reversed.`
  }
  if (divergenceAnalysis.label === 'uncertainty_conflict') {
    return 'Technical and context signals conflicted, so no clear expectation formed.'
  }
  return 'Not enough aligned directional evidence to form a clear expectation.'
}

function directionTone(direction: string): 'success' | 'warning' | 'danger' | 'neutral' {
  if (direction === 'up') return 'success'
  if (direction === 'down') return 'danger'
  return 'neutral'
}

function voteTone(value: string): 'success' | 'danger' | 'neutral' {
  if (value === 'positive') return 'success'
  if (value === 'negative') return 'danger'
  return 'neutral'
}

function voteIcon(value: string): '↗' | '↘' | '→' {
  if (value === 'positive') return '↗'
  if (value === 'negative') return '↘'
  return '→'
}

function buildDivergenceVotes(divergenceAnalysis?: DivergenceAnalysis | null) {
  if (!divergenceAnalysis) return []

  return [
    {
      label: 'Technical',
      value: divergenceAnalysis.signal_votes.technical,
      tone: voteTone(divergenceAnalysis.signal_votes.technical),
      arrow: voteIcon(divergenceAnalysis.signal_votes.technical),
      tooltipMessage: divergenceVoteCopy.Technical,
    },
    {
      label: 'Context',
      value: divergenceAnalysis.signal_votes.context,
      tone: voteTone(divergenceAnalysis.signal_votes.context),
      arrow: voteIcon(divergenceAnalysis.signal_votes.context),
      tooltipMessage: divergenceVoteCopy.Context,
    },
    {
      label: 'Trajectory',
      value: divergenceAnalysis.signal_votes.trajectory,
      tone: voteTone(divergenceAnalysis.signal_votes.trajectory),
      arrow: voteIcon(divergenceAnalysis.signal_votes.trajectory),
      tooltipMessage: divergenceVoteCopy.Trajectory,
    },
    {
      label: 'Shared',
      value: divergenceAnalysis.signal_votes.shared_context,
      tone: voteTone(divergenceAnalysis.signal_votes.shared_context),
      arrow: voteIcon(divergenceAnalysis.signal_votes.shared_context),
      tooltipMessage: divergenceVoteCopy.Shared,
    },
  ]
}
</script>

<style scoped>
.insight-narrative {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 13.5rem;
  gap: 1rem;
  align-items: start;
  --rail-border: rgba(148, 163, 184, 0.22);
  --rail-shell: linear-gradient(160deg, rgba(255, 255, 255, 0.045), rgba(148, 163, 184, 0.02)), var(--bg-secondary);
  --rail-shell-shadow: 0 12px 28px rgba(15, 23, 42, 0.18);
  --panel-border: rgba(148, 163, 184, 0.18);
  --panel-surface: linear-gradient(160deg, rgba(255, 255, 255, 0.035), rgba(148, 163, 184, 0.02)), var(--bg-secondary);
  --panel-shell: linear-gradient(180deg, rgba(255, 255, 255, 0.025), rgba(148, 163, 184, 0.012));
  --panel-shell-shadow: 0 10px 24px rgba(15, 23, 42, 0.16);
  --panel-copy: var(--text-primary);
  --panel-muted: var(--text-secondary);
  --panel-chip: rgba(148, 163, 184, 0.1);
  --panel-chip-text: var(--text-secondary);
}

:global(html[data-theme='light']) .insight-narrative {
  --rail-shell: linear-gradient(160deg, rgba(248, 250, 252, 0.94), rgba(226, 232, 240, 0.84));
  --rail-shell-shadow: 0 12px 24px rgba(148, 163, 184, 0.14);
  --panel-border: rgba(148, 163, 184, 0.24);
  --panel-surface: linear-gradient(160deg, rgba(255, 255, 255, 0.96), rgba(248, 250, 252, 0.92));
  --panel-shell: linear-gradient(180deg, rgba(255, 255, 255, 0.55), rgba(241, 245, 249, 0.76));
  --panel-shell-shadow: 0 10px 24px rgba(148, 163, 184, 0.12);
  --panel-copy: #334155;
  --panel-muted: #64748b;
  --panel-chip: rgba(148, 163, 184, 0.16);
  --panel-chip-text: #475569;
}

.insight-rail {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  min-width: 0;
  justify-self: end;
  width: 100%;
  max-width: 13.5rem;
}

.trajectory-strip {
  position: relative;
  width: 100%;
  padding: 0.85rem 0.9rem 0.95rem;
  border: 1px solid var(--rail-border);
  border-radius: 1rem;
  background:
    radial-gradient(circle at top right, rgba(125, 211, 252, 0.18), transparent 55%),
    var(--rail-shell);
  box-shadow: var(--rail-shell-shadow);
  overflow: hidden;
}

.section-label {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}

.trajectory-grid {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-start;
  gap: 0.45rem;
  max-width: 100%;
}

.divergence-infographic {
  position: relative;
  border-radius: 1.1rem;
  padding: 0.9rem;
  border: 1px solid var(--panel-border);
  box-shadow: var(--panel-shell-shadow);
  overflow: hidden;
  background:
    radial-gradient(circle at top right, rgba(125, 211, 252, 0.18), transparent 55%),
    var(--panel-surface);
}

.divergence-infographic__glow {
  position: absolute;
  inset: auto auto -55% -30%;
  width: 8rem;
  height: 8rem;
  border-radius: 999px;
  background: radial-gradient(circle, rgba(125, 211, 252, 0.18), transparent 68%);
  pointer-events: none;
}

.tone-success .divergence-infographic {
  background:
    radial-gradient(circle at top right, rgba(34, 197, 94, 0.16), transparent 55%),
    var(--panel-surface);
}

.tone-success .divergence-infographic__glow {
  background: radial-gradient(circle, rgba(34, 197, 94, 0.18), transparent 68%);
}

.tone-warning .divergence-infographic__glow {
  background: radial-gradient(circle, rgba(125, 211, 252, 0.18), transparent 68%);
}

.tone-danger .divergence-infographic__glow {
  background: radial-gradient(circle, rgba(125, 211, 252, 0.18), transparent 68%);
}

.divergence-infographic__header {
  position: relative;
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: flex-start;
  margin-bottom: 0.9rem;
}

.divergence-title {
  font-size: 0.82rem;
  line-height: 1;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.divergence-seal {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 4.9rem;
  height: 1.65rem;
  padding: 0 0.5rem;
  border-radius: 999px;
  font-size: 0.58rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  white-space: nowrap;
  background: rgba(125, 211, 252, 0.24);
  color: #e0f2fe;
}

.seal-match {
  background: rgba(34, 197, 94, 0.3);
  color: #dcfce7;
}

.seal-no-match {
  background: rgba(125, 211, 252, 0.26);
  color: #e0f2fe;
}

.divergence-diagram {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 0.35rem;
  align-items: center;
  margin-bottom: 0.65rem;
}

.diagram-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 3.2rem;
}

.diagram-percent {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 3.2rem;
  height: 3.2rem;
  border-radius: 999px;
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--text-primary);
  background:
    radial-gradient(circle at top, rgba(255, 255, 255, 0.18), transparent 55%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.13), rgba(255, 255, 255, 0.04));
  box-shadow: inset 0 0 0 1px var(--panel-border);
}

.tone-success .diagram-percent {
  background:
    radial-gradient(circle at top, rgba(255, 255, 255, 0.18), transparent 55%),
    linear-gradient(180deg, rgba(34, 197, 94, 0.2), rgba(34, 197, 94, 0.08));
  color: #86efac;
}

.tone-warning .diagram-percent {
  background:
    radial-gradient(circle at top, rgba(255, 255, 255, 0.18), transparent 55%),
    linear-gradient(180deg, rgba(245, 158, 11, 0.22), rgba(245, 158, 11, 0.08));
  color: #fbbf24;
}

.tone-danger .diagram-percent {
  background:
    radial-gradient(circle at top, rgba(255, 255, 255, 0.18), transparent 55%),
    linear-gradient(180deg, rgba(239, 68, 68, 0.22), rgba(239, 68, 68, 0.08));
  color: #fca5a5;
}

.diagram-arrow {
  margin-top: 0.25rem;
  font-size: 1rem;
  line-height: 1;
  color: var(--panel-muted);
}

.tone-success .diagram-arrow {
  color: #86efac;
}

.tone-warning .diagram-arrow {
  color: #fbbf24;
}

.tone-danger .diagram-arrow {
  color: #fca5a5;
}

.divergence-copy {
  margin: 0 0 0.8rem;
  line-height: 1.45;
  font-size: 0.78rem;
  color: var(--panel-copy);
}

.divergence-votes {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem 0.7rem;
  margin-bottom: 0.65rem;
}

.divergence-note {
  margin: 0;
  font-size: 0.66rem;
  line-height: 1.35;
  color: var(--panel-muted);
}

.insight-content {
  min-width: 0;
}

.insight-badges {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
}

.insight-summary {
  margin-bottom: 0.75rem;
  line-height: 1.6;
}

.insight-technical {
  margin-bottom: 0.75rem;
  font-size: 0.85rem;
  line-height: 1.5;
}

.footer-text {
  margin: 0;
  font-size: 0.85rem;
  line-height: 1.5;
}

.footnote-list {
  margin: 0;
  padding-left: 1rem;
}

.footnote-list li {
  margin-bottom: 0.35rem;
  font-size: 0.85rem;
  line-height: 1.5;
}

.footnote-link {
  color: inherit;
  text-decoration: underline;
}

@media (max-width: 720px) {
  .insight-narrative {
    grid-template-columns: 1fr;
  }

  .trajectory-strip {
    max-width: none;
  }

  .insight-rail {
    max-width: none;
    justify-self: stretch;
  }

  .divergence-diagram {
    grid-template-columns: 1fr;
  }

  .diagram-center {
    min-width: 0;
  }
}
</style>
