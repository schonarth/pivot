<template>
  <div>
    <div class="page-header">
      <h1>New Portfolio</h1>
    </div>
    <div
      class="card"
      style="max-width: 500px;"
    >
      <div
        v-if="error"
        class="alert-danger"
      >
        {{ error }}
      </div>
      <div class="form-group">
        <label for="name">Name</label>
        <input
          id="name"
          v-model="name"
          type="text"
          placeholder="My BR Portfolio"
          required
        >
      </div>
      <div class="form-group">
        <label for="market">Market</label>
        <select
          id="market"
          v-model="market"
        >
          <option value="BR">
            Brazil (BRL)
          </option>
          <option value="US">
            United States (USD)
          </option>
          <option value="UK">
            United Kingdom (GBP)
          </option>
          <option value="EU">
            European Union (EUR)
          </option>
        </select>
      </div>
      <div class="form-group">
        <label for="capital">Initial Capital</label>
        <input
          id="capital"
          v-model="initialCapital"
          type="text"
          inputmode="decimal"
          placeholder="10000.00 or 10.000,00"
          required
        >
      </div>
      <button
        class="btn"
        :disabled="loading"
        @click="handleCreate"
      >
        <span
          v-if="loading"
          class="spinner"
        />
        Create Portfolio
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { usePortfolioStore } from '@/stores/portfolios'
import { parseNumericInput } from '@/utils/numbers'

const router = useRouter()
const portfolioStore = usePortfolioStore()

const name = ref('')
const market = ref('BR')
const initialCapital = ref('10000.00')
const error = ref('')
const loading = ref(false)

async function handleCreate() {
  error.value = ''
  loading.value = true
  try {
    const portfolio = await portfolioStore.createPortfolio(name.value, market.value, parseNumericInput(initialCapital.value))
    router.push(`/portfolios/${portfolio.id}`)
  } catch (e: any) {
    error.value = e.response?.data?.error?.message || 'Failed to create portfolio'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.alert-danger { background: rgba(239,68,68,0.15); color: var(--danger); padding: 0.75rem; border-radius: 6px; margin-bottom: 1rem; }
</style>