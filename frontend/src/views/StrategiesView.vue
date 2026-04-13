<template>
  <div>
    <div class="page-header">
      <h1>Automated Strategies</h1>
      <button class="btn btn-sm" @click="showCreate = true">Add Strategy</button>
    </div>

    <div v-if="showCreate" class="card" style="margin-bottom: 2rem;">
      <h3 style="margin-bottom: 1rem;">Create New Strategy</h3>
      <div class="form-group">
        <label for="rule-select">Select Rule</label>
        <select id="rule-select" v-model="selectedRuleId" class="form-control">
          <option value="">-- Choose a strategy rule --</option>
          <option v-for="rule in rules" :key="rule.id" :value="rule.id">
            {{ rule.name }} - {{ rule.description }}
          </option>
        </select>
      </div>

      <div v-if="selectedRule" class="form-group" style="background: rgba(0, 0, 0, 0.05); padding: 1rem; border-radius: 4px; margin-bottom: 1rem;">
        <p style="margin: 0 0 0.5rem 0; font-size: 0.875rem; color: #666;">
          <strong>{{ selectedRule.name }}</strong><br />
          {{ selectedRule.description }}
        </p>
        <div style="font-size: 0.75rem; color: #999; margin-top: 0.5rem;">
          Parameters: {{ JSON.stringify(selectedRule.conditions, null, 2) }}
        </div>
      </div>

      <div class="form-group">
        <label>Risk Guardrails</label>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
          <div>
            <label class="form-label" for="max-trades">Max Trades/Day</label>
            <input id="max-trades" v-model.number="guardrails.max_trades_per_day" type="number" class="form-control" min="1" max="100" />
          </div>
          <div>
            <label class="form-label" for="max-position">Max Position Size %</label>
            <input id="max-position" v-model.number="guardrails.max_position_size_pct" type="number" class="form-control" min="1" max="50" />
          </div>
          <div>
            <label class="form-label" for="stop-loss">Stop Loss %</label>
            <input id="stop-loss" v-model.number="guardrails.stop_loss_pct" type="number" class="form-control" min="1" max="20" />
          </div>
          <div>
            <label class="form-label" for="max-exposure">Max Portfolio Exposure %</label>
            <input id="max-exposure" v-model.number="guardrails.max_portfolio_exposure_pct" type="number" class="form-control" min="10" max="100" />
          </div>
        </div>
      </div>

      <div style="display: flex; gap: 0.5rem;">
        <button class="btn btn-sm" @click="handleCreateStrategy" :disabled="creating || !selectedRuleId">Create Strategy</button>
        <button class="btn btn-secondary btn-sm" @click="showCreate = false">Cancel</button>
      </div>
    </div>

    <div v-if="strategies.length === 0" class="card">
      <p class="text-muted">No strategies enabled yet. Create one to get started with automated trading.</p>
    </div>

    <div v-for="strategy in strategies" :key="strategy.id" class="card" style="margin-bottom: 1rem;">
      <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
        <div>
          <h3 style="margin: 0 0 0.25rem 0;">{{ strategy.rule.name }}</h3>
          <p style="margin: 0; font-size: 0.875rem; color: #666;">{{ strategy.rule.description }}</p>
        </div>
        <div style="display: flex; gap: 0.5rem;">
          <span v-if="strategy.enabled" class="badge badge-success">Active</span>
          <span v-else class="badge">Inactive</span>
          <span v-if="strategy.backtest_approved_at" class="badge badge-info">Approved</span>
          <span v-else class="badge">Pending Approval</span>
        </div>
      </div>

      <div v-if="strategy.backtest_approved_at" style="margin-bottom: 1rem;">
        <p style="margin: 0; font-size: 0.75rem; color: #999;">
          Backtest approved: {{ new Date(strategy.backtest_approved_at).toLocaleDateString() }}
        </p>
      </div>

      <div style="display: flex; gap: 0.5rem; margin-bottom: 1rem;">
        <button v-if="!strategy.backtest_approved_at" class="btn btn-sm" @click="showBacktestDialog(strategy)">
          Run Backtest
        </button>
        <button v-if="!strategy.backtest_approved_at && hasRecentBacktest(strategy)" class="btn btn-success btn-sm" @click="handleApproveBacktest(strategy)">
          Approve & Activate
        </button>
        <button v-if="strategy.enabled" class="btn btn-danger btn-sm" @click="handleDisableStrategy(strategy)">
          Disable
        </button>
        <button class="btn btn-secondary btn-sm" @click="activeStrategyId = activeStrategyId === strategy.id ? null : strategy.id">
          {{ activeStrategyId === strategy.id ? 'Hide' : 'View' }} Details
        </button>
      </div>

      <div v-if="activeStrategyId === strategy.id" style="border-top: 1px solid #eee; padding-top: 1rem;">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
          <div>
            <p style="margin: 0 0 0.25rem 0; font-size: 0.75rem; color: #999; text-transform: uppercase;">Risk Settings</p>
            <ul style="margin: 0; padding: 0; list-style: none; font-size: 0.875rem;">
              <li>Max Trades/Day: <strong>{{ strategy.settings.max_trades_per_day || 10 }}</strong></li>
              <li>Max Position Size: <strong>{{ strategy.settings.max_position_size_pct || 10 }}%</strong></li>
              <li>Stop Loss: <strong>{{ strategy.settings.stop_loss_pct || 5 }}%</strong></li>
              <li>Max Exposure: <strong>{{ strategy.settings.max_portfolio_exposure_pct || 50 }}%</strong></li>
            </ul>
          </div>
          <div>
            <p style="margin: 0 0 0.25rem 0; font-size: 0.75rem; color: #999; text-transform: uppercase;">Recent Activity</p>
            <div v-if="recentTrades[strategy.id]?.length" style="font-size: 0.875rem;">
              <div v-for="trade in recentTrades[strategy.id].slice(0, 3)" :key="trade.id" style="margin-bottom: 0.25rem;">
                <span :class="trade.action === 'BUY' ? 'text-success' : 'text-danger'">
                  {{ trade.action }}
                </span>
                - {{ new Date(trade.executed_at).toLocaleDateString() }}
              </div>
            </div>
            <p v-else style="margin: 0; color: #999; font-size: 0.875rem;">No trades yet</p>
          </div>
        </div>

        <div>
          <p style="margin: 0 0 0.5rem 0; font-size: 0.75rem; color: #999; text-transform: uppercase;">Backtest History</p>
          <table v-if="backtests[strategy.id]?.length" style="font-size: 0.875rem; width: 100%;">
            <thead>
              <tr style="border-bottom: 1px solid #eee;">
                <th style="text-align: left; padding: 0.25rem 0;">Date Range</th>
                <th style="text-align: left; padding: 0.25rem 0;">Status</th>
                <th style="text-align: left; padding: 0.25rem 0;">Trades</th>
                <th style="text-align: left; padding: 0.25rem 0;">P&L</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="backtest in backtests[strategy.id].slice(0, 3)" :key="backtest.id" style="border-bottom: 1px solid #f0f0f0;">
                <td style="padding: 0.25rem 0;">{{ backtest.date_from }} to {{ backtest.date_to }}</td>
                <td style="padding: 0.25rem 0;">
                  <span :class="{
                    'text-success': backtest.status === 'completed',
                    'text-danger': backtest.status === 'failed',
                    'text-muted': backtest.status === 'pending',
                  }">
                    {{ backtest.status }}
                  </span>
                </td>
                <td style="padding: 0.25rem 0;">{{ backtest.result?.total_trades || '-' }}</td>
                <td style="padding: 0.25rem 0;">{{ backtest.result?.total_pnl ? formatCurrency(String(backtest.result.total_pnl)) : '-' }}</td>
              </tr>
            </tbody>
          </table>
          <p v-else style="margin: 0; color: #999; font-size: 0.875rem;">No backtests yet</p>
        </div>
      </div>
    </div>

    <!-- Backtest Dialog -->
    <div v-if="backtestingStrategy" style="
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
    ">
      <div class="card" style="width: 100%; max-width: 400px;">
        <h3 style="margin-top: 0;">Run Backtest</h3>
        <div class="form-group">
          <label for="backtest-from">From Date</label>
          <input id="backtest-from" v-model="backtestDateFrom" type="date" class="form-control" />
        </div>
        <div class="form-group">
          <label for="backtest-to">To Date</label>
          <input id="backtest-to" v-model="backtestDateTo" type="date" class="form-control" />
        </div>
        <div style="display: flex; gap: 0.5rem;">
          <button class="btn btn-sm" @click="handleRunBacktest" :disabled="backtesting">
            {{ backtesting ? 'Running...' : 'Run Backtest' }}
          </button>
          <button class="btn btn-secondary btn-sm" @click="backtestingStrategy = null">Cancel</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import * as strategiesApi from '@/api/strategies'
import type { StrategyRule, StrategyInstance, BacktestScenario, StrategyTrade } from '@/api/strategies'
import { formatCurrency } from '@/utils/numbers'

const props = defineProps<{ id?: string | string[] }>()
const route = useRoute()

const getPortfolioId = () => {
  const routePortfolioId = route.params.id as string | string[] | undefined
  const propsId = props.id ?? routePortfolioId
  const rawId = Array.isArray(propsId) ? propsId[0] : propsId
  return rawId ?? ''
}

const portfolioId = computed(() => getPortfolioId())

const rules = ref<StrategyRule[]>([])
const strategies = ref<StrategyInstance[]>([])
const backtests = ref<Record<string, BacktestScenario[]>>({})
const recentTrades = ref<Record<string, StrategyTrade[]>>({})

const showCreate = ref(false)
const selectedRuleId = ref('')
const activeStrategyId = ref<string | null>(null)
const backtestingStrategy = ref<StrategyInstance | null>(null)
const backtestDateFrom = ref('')
const backtestDateTo = ref('')

const creating = ref(false)
const backtesting = ref(false)

const guardrails = ref({
  max_trades_per_day: 10,
  max_position_size_pct: 10,
  stop_loss_pct: 5,
  max_portfolio_exposure_pct: 50,
})

const selectedRule = computed(() => rules.value.find(r => r.id === selectedRuleId.value))

function hasRecentBacktest(strategy: StrategyInstance): boolean {
  const strat = backtests.value[strategy.id]
  return strat?.some(b => b.status === 'completed') ?? false
}

function showBacktestDialog(strategy: StrategyInstance) {
  backtestingStrategy.value = strategy
  const today = new Date()
  backtestDateTo.value = today.toISOString().split('T')[0]
  const sixMonthsAgo = new Date(today.getTime() - 180 * 24 * 60 * 60 * 1000)
  backtestDateFrom.value = sixMonthsAgo.toISOString().split('T')[0]
}

async function handleCreateStrategy() {
  if (!selectedRuleId.value) return

  creating.value = true
  try {
    const newStrategy = await strategiesApi.createStrategyInstance(
      portfolioId.value,
      selectedRuleId.value,
      guardrails.value,
    )
    strategies.value.push(newStrategy)
    showCreate.value = false
    selectedRuleId.value = ''
  } catch (error) {
    console.error('Failed to create strategy:', error)
  } finally {
    creating.value = false
  }
}

async function handleRunBacktest() {
  if (!backtestingStrategy.value) return

  backtesting.value = true
  try {
    const scenario = await strategiesApi.runBacktest(
      backtestingStrategy.value.id,
      backtestDateFrom.value,
      backtestDateTo.value,
    )
    backtests.value[backtestingStrategy.value.id] = [scenario, ...(backtests.value[backtestingStrategy.value.id] || [])]
    backtestingStrategy.value = null
  } catch (error) {
    console.error('Failed to run backtest:', error)
  } finally {
    backtesting.value = false
  }
}

async function handleApproveBacktest(strategy: StrategyInstance) {
  try {
    const updated = await strategiesApi.approveBacktest(strategy.id)
    const idx = strategies.value.findIndex(s => s.id === strategy.id)
    if (idx >= 0) {
      strategies.value[idx] = updated
    }
  } catch (error) {
    console.error('Failed to approve backtest:', error)
  }
}

async function handleDisableStrategy(strategy: StrategyInstance) {
  try {
    const updated = await strategiesApi.disableStrategy(strategy.id)
    const idx = strategies.value.findIndex(s => s.id === strategy.id)
    if (idx >= 0) {
      strategies.value[idx] = updated
    }
  } catch (error) {
    console.error('Failed to disable strategy:', error)
  }
}

async function loadData() {
  try {
    rules.value = await strategiesApi.getStrategyRules()
    strategies.value = await strategiesApi.getStrategyInstances(portfolioId.value)

    for (const strategy of strategies.value) {
      backtests.value[strategy.id] = await strategiesApi.getBacktests(strategy.id)
      recentTrades.value[strategy.id] = await strategiesApi.getStrategyTrades(strategy.id)
    }
  } catch (error) {
    console.error('Failed to load strategies:', error)
  }
}

onMounted(() => {
  loadData()
})
</script>
