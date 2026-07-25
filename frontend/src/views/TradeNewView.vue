<template>
  <div>
    <div class="page-header">
      <h1>New Trade</h1>
      <router-link
        :to="`/portfolios/${portfolioId}`"
        class="btn btn-secondary"
      >
        Back to Portfolio
      </router-link>
    </div>
    <div
      class="card"
      style="max-width: 600px;"
    >
      <div
        v-if="error"
        class="alert-danger"
      >
        {{ error }}
        <ul
          v-if="guardrailViolations.length"
          style="margin: 0.5rem 0 0 1rem;"
        >
          <li
            v-for="violation in guardrailViolations"
            :key="violation"
          >
            {{ violation }}
          </li>
        </ul>
      </div>
      <div class="form-group">
        <label>Action</label>
        <select v-model="action">
          <option value="BUY">
            BUY
          </option>
          <option value="SELL">
            SELL
          </option>
        </select>
      </div>
      <div class="form-group">
        <label>Search Asset</label>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Type to search assets..."
          @input="handleSearchInput"
        >
        <div
          v-if="searchResults.length"
          style="margin-top: 0.5rem; max-height: 200px; overflow-y: auto; border: 1px solid var(--border); border-radius: 6px;"
        >
          <div
            v-for="a in searchResults"
            :key="a.id"
            style="padding: 0.5rem 0.75rem; cursor: pointer; border-bottom: 1px solid var(--border);"
            @click="selectAsset(a)"
          >
            <strong>{{ a.display_symbol }}</strong> - {{ a.name }}
            <MarketBadge
              :market="a.market"
              style="margin-left: 0.5rem;"
            />
          </div>
        </div>
      </div>
      <div
        v-if="selectedAsset"
        class="card"
        style="margin-bottom: 1rem;"
      >
        <div style="display: flex; justify-content: space-between;">
          <div>
            <strong>{{ selectedAsset.display_symbol }}</strong>
            <span
              v-if="currentPrice?.market_open"
              class="badge badge-success"
              style="margin-left: 0.5rem;"
            >Market Open</span>
            <span
              v-else-if="currentPrice"
              class="badge badge-warning"
              style="margin-left: 0.5rem;"
            >Market Closed</span>
          </div>
          <span>{{ selectedAsset.name }}</span>
        </div>
        <div
          v-if="currentPrice"
          style="display: flex; justify-content: space-between; margin-top: 0.5rem;"
        >
          <div>
            <span>Current Price: </span>
            <strong>{{ currentPrice.currency }} {{ Number(currentPrice.price).toFixed(2) }}</strong>
          </div>
          <div
            v-if="currentPosition > 0"
            :class="{ 'negative-balance': disallowSell }"
          >
            <span>Current position: </span>
            <strong>{{ currentPosition }}</strong>
          </div>
        </div>
      </div>
      <div class="form-group">
        <label>Quantity</label>
        <input
          v-model.number="quantity"
          type="number"
          min="1"
          step="1"
        >
      </div>
      <div class="form-group">
        <label>Rationale (optional)</label>
        <input
          v-model="rationale"
          type="text"
          placeholder="Manual operation"
        >
      </div>
      <div
        v-if="preview"
        class="card"
        style="margin-bottom: 1rem;"
      >
        <div style="display: flex; justify-content: space-between;">
          <span>Gross Value:</span><span>{{ preview.gross }}</span>
        </div>
        <div style="display: flex; justify-content: space-between;">
          <span>Fees:</span><span>{{ preview.fees }}</span>
        </div>
        <div style="display: flex; justify-content: space-between;">
          <span>Net Cash Impact:</span><span>{{ preview.net }}</span>
        </div>
        <div style="display: flex; justify-content: space-between;">
          <span>Balance after transaction:</span>
          <span :class="{ 'negative-balance': projectedBalance !== null && projectedBalance < 0 }">
            {{ projectedBalanceDisplay }}
          </span>
        </div>
      </div>
      <div class="trade-actions">
        <button
          class="btn"
          :disabled="!selectedAsset || !quantity || loading || disallowBuy || disallowSell"
          @click="handleSubmit()"
        >
          <span
            v-if="loading"
            class="spinner"
          />
          {{ action }} Trade
        </button>
        <button
          class="btn btn-secondary"
          :disabled="!selectedAsset || !quantity || validationLoading"
          @click="handleValidation"
        >
          <span
            v-if="validationLoading"
            class="spinner"
          />
          {{ t.shouldI }}
        </button>
        <button
          v-if="canBypassGuardrails"
          class="btn btn-secondary"
          :disabled="loading"
          @click="handleSubmit(true)"
        >
          Proceed Anyway
        </button>
      </div>
      <div
        v-if="validationError"
        class="advisory-panel advisory-panel-danger"
      >
        {{ validationError }}
      </div>
      <div
        v-if="latestRecommendation"
        class="advisory-panel"
      >
        <h2 :class="recommendationDisplay.class">
          {{ recommendationDisplay.label }}
        </h2>
        <p>{{ latestRecommendation.rationale }}</p>
          <div
            v-if="latestRecommendation.scenario_frames.length"
            class="scenario-section"
        >
          <h3>{{ t.scenarios }}</h3>
          <div class="scenario-list">
            <div
              v-for="frame in sortedScenarioFrames(latestRecommendation.scenario_frames)"
              :key="frame.id"
              class="scenario-frame"
            >
              <div class="scenario-frame-header">
                <strong>{{ scenarioCaseLabel(frame.scenario_case) }}</strong>
                <span>{{ scenarioDirectionLabel(frame.direction) }} for {{ latestRecommendation.action }}</span>
              </div>
              <span>{{ t.confidence }}: {{ frame.confidence_band }}</span>
              <div
                v-if="scenarioEvidenceLines(frame).length"
                class="scenario-evidence"
              >
                <span
                  v-for="item in scenarioEvidenceLines(frame)"
                  :key="`${frame.id}-${item}`"
                >{{ item }}</span>
              </div>
              <p>
                <template
                  v-for="(segment, index) in riskNoteSegments(frame.risk_notes, latestRecommendation)"
                  :key="`${frame.id}-${index}`"
                >
                  <em v-if="segment.isHeadline">{{ segment.text }}</em>
                  <template v-else>{{ segment.text }}</template>
                </template>
              </p>
            </div>
          </div>
          <EvidenceReview
            :recommendation-id="latestRecommendation.id"
            :enable-source-stance-controls="evidenceSourceStanceOverride"
          />
        </div>
      </div>
      <div
        v-if="recommendations.length"
        class="advisory-panel"
      >
        <strong>{{ t.previousRecommendations }}</strong>
        <div
          class="recommendations-table-viewport"
        >
          <table class="recommendations-table">
            <thead>
              <tr>
                <th>{{ t.asset }}</th>
                <th>{{ t.trade }}</th>
                <th>{{ t.amount }}</th>
                <th>{{ t.verdict }}</th>
                <th>{{ t.timestamp }}</th>
              </tr>
            </thead>
            <tbody>
              <template
                v-for="item in recommendations"
                :key="item.id"
              >
                <tr>
                  <td>
                    <button
                      class="recommendation-toggle"
                      :class="{ expanded: isRecommendationExpanded(item.id) }"
                      type="button"
                      :aria-expanded="isRecommendationExpanded(item.id)"
                      :aria-label="isRecommendationExpanded(item.id) ? t.hideDetails : t.showDetails"
                      @click="toggleRecommendation(item.id)"
                    >
                      <span
                        class="chevron-triangle"
                        aria-hidden="true"
                      />
                    </button>
                    {{ item.asset_display_symbol }}
                  </td>
                  <td>{{ item.action }}</td>
                  <td>{{ item.quantity }}</td>
                  <td>
                    <span :class="displayForVerdict(item.verdict).class">
                      {{ displayForVerdict(item.verdict).label }}
                    </span>
                  </td>
                  <td>{{ formatDate(item.recorded_at) }}</td>
                </tr>
                <tr
                  v-if="isRecommendationExpanded(item.id)"
                  class="recommendation-detail-row"
                >
                  <td colspan="5">
                    <p>{{ item.rationale }}</p>
                    <div
                      v-if="item.scenario_frames.length"
                      class="scenario-section"
                    >
                      <h3>{{ t.scenarios }}</h3>
                      <div class="scenario-list">
                        <div
                          v-for="frame in sortedScenarioFrames(item.scenario_frames)"
                          :key="frame.id"
                          class="scenario-frame"
                        >
                          <div class="scenario-frame-header">
                            <strong>{{ scenarioCaseLabel(frame.scenario_case) }}</strong>
                            <span>{{ scenarioDirectionLabel(frame.direction) }} for {{ item.action }}</span>
                          </div>
                          <span>{{ t.confidence }}: {{ frame.confidence_band }}</span>
                          <div
                            v-if="scenarioEvidenceLines(frame).length"
                            class="scenario-evidence"
                          >
                            <span
                              v-for="item in scenarioEvidenceLines(frame)"
                              :key="`${frame.id}-${item}`"
                            >{{ item }}</span>
                          </div>
                          <p>
                            <template
                              v-for="(segment, index) in riskNoteSegments(frame.risk_notes, item)"
                              :key="`${frame.id}-${index}`"
                            >
                              <em v-if="segment.isHeadline">{{ segment.text }}</em>
                              <template v-else>{{ segment.text }}</template>
                            </template>
                          </p>
                        </div>
                      </div>
                    </div>
                    <EvidenceReview
                      :recommendation-id="item.id"
                      :enable-source-stance-controls="evidenceSourceStanceOverride"
                    />
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import MarketBadge from '@/components/MarketBadge.vue'
import EvidenceReview from '@/components/EvidenceReview.vue'
import { searchAssets as apiSearchAssets, getAssetPrice, getAsset } from '@/api/assets'
import { createTrade } from '@/api/trades'
import { getStrategyRecommendations, validateStrategyCandidate } from '@/api/ai'
import { getPortfolio, getPortfolioSummary } from '@/api/portfolios'
import type { Asset, AssetQuote, Portfolio, PortfolioSummary, StrategyRecommendation } from '@/types'

const t = {
  shouldI: 'Should I?',
  previousRecommendations: 'Previous recommendations',
  validationFailed: 'Validation failed',
  amount: 'Amount',
  asset: 'Asset',
  base: 'Base case',
  bull: 'Bull case',
  bear: 'Bear case',
  conditional: 'conditional',
  confidence: 'Confidence',
  adverse: 'adverse',
  hideDetails: 'Hide',
  scenarios: 'Scenarios',
  supportive: 'supportive',
  showDetails: 'Details',
  timestamp: 'Timestamp',
  trade: 'Trade',
  verdict: 'Verdict',
}

const props = defineProps<{ id?: string | string[] }>()
const route = useRoute()
const router = useRouter()

const routePortfolioId = route.params.id as string | string[] | undefined
const propsId = props.id ?? routePortfolioId
const rawId = Array.isArray(propsId) ? propsId[0] : propsId
const portfolioId = rawId ?? ''

const preselectedAssetId = (route.query.asset as string) || null
const evidenceSourceStanceOverride = route.query.evidenceSourceStanceOverride === 'true'

const action = ref<'BUY' | 'SELL'>('BUY')
const searchQuery = ref('')
const searchResults = ref<Asset[]>([])
const selectedAsset = ref<Asset | null>(null)
const currentPrice = ref<AssetQuote | null>(null)
const portfolio = ref<Portfolio | null>(null)
const portfolioSummary = ref<PortfolioSummary | null>(null)
const quantity = ref<number | null>(null)
const rationale = ref('')
const error = ref('')
const guardrailViolations = ref<string[]>([])
const canBypassGuardrails = ref(false)
const loading = ref(false)
const validationLoading = ref(false)
const validationError = ref('')
const latestRecommendation = ref<StrategyRecommendation | null>(null)
const recommendations = ref<StrategyRecommendation[]>([])
const expandedRecommendationIds = ref<Set<string>>(new Set())
const feeRate = ref<number>(0)

type ApiError = {
  response?: {
    data?: {
      error?: {
        message?: string
        violations?: string[]
        allow_bypass?: boolean
      }
    }
  }
}

const preview = computed(() => {
  if (!selectedAsset.value || !quantity.value || !currentPrice.value) return null
  const price = Number(currentPrice.value.price)
  const qty = quantity.value
  const gross = price * qty
  const fees = gross * feeRate.value
  const net = action.value === 'BUY' ? -(gross + fees) : gross - fees
  return {
    gross: gross.toFixed(2),
    fees: fees.toFixed(2),
    net: net.toFixed(2),
  }
})

const projectedBalance = computed(() => {
  if (!preview.value || !portfolio.value) return null
  return Number(portfolio.value.current_cash) + Number(preview.value.net)
})

const projectedBalanceDisplay = computed(() => {
  if (projectedBalance.value === null || !portfolio.value) return '--'
  return `${portfolio.value.base_currency} ${projectedBalance.value.toFixed(2)}`
})

const disallowBuy = computed(() => action.value === 'BUY' && projectedBalance.value !== null && projectedBalance.value < 0)
const currentPosition = computed(() => {
  if (!selectedAsset.value) return 0
  return portfolioSummary.value?.positions.find(position => position.asset_id === selectedAsset.value?.id)?.quantity ?? 0
})
const disallowSell = computed(() => action.value === 'SELL' && quantity.value !== null && quantity.value > currentPosition.value)
const recommendationDisplay = computed(() => {
  if (!latestRecommendation.value) return displayForVerdict('defer')
  return displayForVerdict(latestRecommendation.value.verdict)
})
let searchTimeout: ReturnType<typeof setTimeout>

onMounted(async () => {
  try {
    portfolio.value = await getPortfolio(portfolioId)
    portfolioSummary.value = await getPortfolioSummary(portfolioId)
    feeRate.value = portfolio.value.market === 'BR' ? 0.0003 : portfolio.value.market === 'US' ? 0 : 0.001
  } catch {
    portfolio.value = null
    portfolioSummary.value = null
  }
  try {
    recommendations.value = await getStrategyRecommendations(portfolioId)
  } catch {
    recommendations.value = []
  }

  if (preselectedAssetId) {
    try {
      const asset = await getAsset(preselectedAssetId)
      await selectAsset(asset)
    } catch {
      selectedAsset.value = null
    }
  }
})

function handleSearchInput() {
  if (selectedAsset.value && searchQuery.value !== selectedAsset.value.display_symbol) {
    selectedAsset.value = null
    currentPrice.value = null
  }
  doSearch()
}

function doSearch() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(async () => {
    if (searchQuery.value.length < 2) {
      searchResults.value = []
      return
    }
    try {
      if (!portfolioId) return
      portfolio.value = await getPortfolio(portfolioId)
      portfolioSummary.value = await getPortfolioSummary(portfolioId)
      searchResults.value = await apiSearchAssets(searchQuery.value, portfolio.value.market)
      feeRate.value = portfolio.value.market === 'BR' ? 0.0003 : portfolio.value.market === 'US' ? 0 : 0.001
    } catch {
      searchResults.value = []
    }
  }, 300)
}

async function selectAsset(asset: Asset) {
  selectedAsset.value = asset
  searchResults.value = []
  searchQuery.value = asset.display_symbol
  try {
    currentPrice.value = await getAssetPrice(asset.id)
  } catch {
    currentPrice.value = null
  }
}

function apiError(error: unknown): ApiError {
  return error as ApiError
}

async function handleSubmit(bypassGuardrails: boolean = false) {
  if (!portfolioId) return
  if (!selectedAsset.value || !quantity.value) return
  if (disallowBuy.value) return
  if (disallowSell.value) return
  error.value = ''
  guardrailViolations.value = []
  canBypassGuardrails.value = false
  loading.value = true
  try {
    await createTrade(
      portfolioId,
      selectedAsset.value.id,
      action.value,
      quantity.value,
      rationale.value || undefined,
      bypassGuardrails,
    )
    router.push(`/portfolios/${portfolioId}`)
  } catch (e: unknown) {
    const responseError = apiError(e).response?.data?.error
    error.value = responseError?.message || 'Trade failed'
    guardrailViolations.value = responseError?.violations || []
    canBypassGuardrails.value = Boolean(responseError?.allow_bypass)
  } finally {
    loading.value = false
  }
}

async function handleValidation() {
  if (!portfolioId) return
  if (!selectedAsset.value || !quantity.value) return
  validationError.value = ''
  validationLoading.value = true
  try {
    latestRecommendation.value = await validateStrategyCandidate({
      portfolio_id: portfolioId,
      asset_id: selectedAsset.value.id,
      action: action.value,
      quantity: quantity.value,
      rationale: rationale.value || undefined,
    })
    recommendations.value = [latestRecommendation.value, ...recommendations.value.filter(item => item.id !== latestRecommendation.value?.id)]
  } catch (e: unknown) {
    validationError.value = apiError(e).response?.data?.error?.message || t.validationFailed
  } finally {
    validationLoading.value = false
  }
}

function formatDate(d: string): string {
  return new Date(d).toLocaleString()
}

function displayForVerdict(verdict: StrategyRecommendation['verdict']) {
  if (verdict === 'approve') return { label: 'Do it', class: 'recommendation-do' }
  if (verdict === 'reject') return { label: "Don't", class: 'recommendation-dont' }
  return { label: 'Not sure', class: 'recommendation-unsure' }
}

function scenarioCaseLabel(scenarioCase: 'base' | 'bull' | 'bear'): string {
  return t[scenarioCase]
}

function scenarioDirectionLabel(direction: string): string {
  if (direction === 'supportive') return t.supportive
  if (direction === 'adverse') return t.adverse
  if (direction === 'conditional') return t.conditional
  return direction
}

function sortedScenarioFrames(
  frames: StrategyRecommendation['scenario_frames'],
): StrategyRecommendation['scenario_frames'] {
  const order = { bull: 0, base: 1, bear: 2 }
  return [...frames].sort((a, b) => order[a.scenario_case] - order[b.scenario_case])
}

type RiskNoteSegment = {
  text: string
  isHeadline: boolean
}

type ContextInputItem = {
  headline?: unknown
}

function scenarioEvidenceLines(frame: StrategyRecommendation['scenario_frames'][number]): string[] {
  const references = [...frame.catalysts, ...frame.invalidating_conditions]
  return Array.from(new Set(
    references
      .filter(item => item.source === 'context_inputs')
      .map(item => item.text)
      .filter(Boolean),
  ))
}

function riskNoteSegments(
  riskNotes: string,
  recommendation: StrategyRecommendation,
): RiskNoteSegment[] {
  const headlines = contextHeadlines(recommendation)
  const segments: RiskNoteSegment[] = []
  let cursor = 0

  while (cursor < riskNotes.length) {
    const nextMatch = headlines
      .map(headline => ({ headline, start: riskNotes.indexOf(headline, cursor) }))
      .filter(match => match.start >= 0)
      .sort((a, b) => a.start - b.start)[0]

    if (!nextMatch) break

    if (nextMatch.start > cursor) {
      segments.push({ text: riskNotes.slice(cursor, nextMatch.start), isHeadline: false })
    }

    let end = nextMatch.start + nextMatch.headline.length
    let text = nextMatch.headline
    const trailingDot = riskNotes.slice(end).match(/^\s*\./)
    if (trailingDot) {
      text += '.'
      end += trailingDot[0].length
    }

    segments.push({ text, isHeadline: true })
    cursor = end
  }

  if (cursor < riskNotes.length) {
    segments.push({ text: riskNotes.slice(cursor), isHeadline: false })
  }

  return segments.length ? segments : [{ text: riskNotes, isHeadline: false }]
}

function contextHeadlines(recommendation: StrategyRecommendation): string[] {
  const items = recommendation.context_inputs.items
  if (!Array.isArray(items)) return []
  return items
    .map(item => (item as ContextInputItem).headline)
    .filter((headline): headline is string => typeof headline === 'string' && Boolean(headline))
}

function isRecommendationExpanded(id: string): boolean {
  return expandedRecommendationIds.value.has(id)
}

function toggleRecommendation(id: string) {
  const next = new Set(expandedRecommendationIds.value)
  if (next.has(id)) {
    next.delete(id)
  } else {
    next.add(id)
  }
  expandedRecommendationIds.value = next
}
</script>

<style scoped>
.alert-danger { background: rgba(239,68,68,0.15); color: var(--danger); padding: 0.75rem; border-radius: 6px; margin-bottom: 1rem; }
.negative-balance { color: var(--danger); }
.trade-actions { display: flex; align-items: center; flex-wrap: wrap; gap: 0.75rem; }
.advisory-panel { margin-top: 1rem; padding: 0.75rem; border: 1px solid var(--border); border-radius: 6px; }
.advisory-panel h2 { font-size: 1.125rem; margin: 0 0 0.5rem; }
.advisory-panel p { margin: 0.5rem 0; }
.scenario-section { margin-top: 0.875rem; }
.scenario-section h3 { font-size: 0.9375rem; margin: 0 0 0.5rem; }
.advisory-panel-danger { color: var(--danger); border-color: var(--danger); }
.recommendation-do { color: #00a651; font-weight: 800; }
.recommendation-dont { color: #e11937; font-weight: 800; }
.recommendation-unsure { color: var(--text); font-weight: 400; }
.recommendations-table-viewport { max-height: 30rem; overflow: auto; margin-top: 0.75rem; }
.recommendations-table { width: 100%; table-layout: fixed; }
.recommendations-table th,
.recommendations-table td { padding: 0.5rem; text-align: left; }
.recommendations-table td { font-size: 0.8125rem; }
.recommendations-table thead th { position: sticky; top: 0; background: var(--card-bg); z-index: 1; }
.recommendation-toggle { appearance: none; background: transparent; border: 0; color: var(--text); cursor: pointer; margin-right: 0.5rem; padding: 0; vertical-align: middle; }
.chevron-triangle { width: 0; height: 0; border-top: 0.35rem solid transparent; border-bottom: 0.35rem solid transparent; border-left: 0.5rem solid currentColor; display: inline-block; transition: transform 0.2s ease; }
.recommendation-toggle.expanded .chevron-triangle { transform: rotate(90deg); }
.recommendation-detail-row td { background: rgba(0,0,0,0.03); }
.recommendation-detail-row p { margin: 0.5rem 0; }
.scenario-list { display: grid; gap: 0.5rem; grid-template-columns: repeat(auto-fit, minmax(10rem, 1fr)); }
.scenario-frame { border: 1px solid var(--border); border-radius: 6px; font-size: 0.8125rem; padding: 0.625rem; }
.scenario-frame-header { display: flex; align-items: baseline; justify-content: space-between; gap: 0.5rem; }
.scenario-frame p { font-size: 0.8125rem; line-height: 1.35; }
.scenario-frame span { display: block; color: var(--text-muted); font-size: 0.75rem; margin-top: 0.125rem; }
.scenario-frame-header span { margin-top: 0; text-align: right; }
.scenario-evidence { display: grid; gap: 0.25rem; margin-top: 0.375rem; }
.scenario-evidence span { color: var(--text); font-size: 0.75rem; line-height: 1.3; }
</style>
