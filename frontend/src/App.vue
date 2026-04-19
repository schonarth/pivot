<template>
  <div id="app-layout">
    <nav
      v-if="auth.isAuthenticated"
      class="navbar"
    >
      <div class="nav-brand">
        <router-link
          to="/"
          class="brand-link"
        >
          <img
            :src="pivotLogo"
            alt="Pivot"
            class="brand-logo"
          >
          <span>Pivot</span>
        </router-link>
      </div>
      <div class="nav-links">
        <router-link to="/">
          Dashboard
        </router-link>
        <router-link to="/assets">
          Assets
        </router-link>
        <router-link to="/discovery">
          Discovery
        </router-link>
        <router-link to="/settings">
          Settings
        </router-link>
      </div>
      <div class="nav-user">
        <div
          v-if="auth.isAuthenticated && aiBudget.enabled"
          class="ai-budget"
          :title="`AI: $${aiBudget.usage_usd} / $${aiBudget.monthly_budget_usd}`"
        >
          <span class="ai-budget-label">AI</span>
          <div class="ai-budget-track">
            <div
              class="ai-budget-fill"
              :style="{ width: `${Math.min(Number(aiBudget.percentage_used || 0), 100)}%`, background: aiBudgetColor }"
            />
          </div>
        </div>
        <span v-if="auth.user">{{ auth.user.username }}</span>
        <button
          class="btn btn-secondary btn-sm"
          @click="handleLogout"
        >
          Logout
        </button>
      </div>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
    <ToastContainer />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useWebSocketStore } from '@/stores/websocket'
import { useNotifications } from '@/composables/useNotifications'
import { getBudget, type AIBudget } from '@/api/ai'
import ToastContainer from '@/components/ToastContainer.vue'

const auth = useAuthStore()
useWebSocketStore()
const { requestPermission } = useNotifications()
const router = useRouter()
const pivotLogo = '/pivot-logo.png'
const aiBudget = reactive<AIBudget>({
  enabled: false,
  monthly_budget_usd: '0.00',
  usage_usd: '0.00',
  remaining_usd: '0.00',
  percentage_used: '0',
  at_limit: false,
  should_warn: false,
})

const aiBudgetColor = computed(() => {
  const used = Number(aiBudget.percentage_used || 0)
  if (used >= 100) return '#dc2626'
  if (used >= 90) return '#f97316'
  if (used >= 50) return '#eab308'
  return '#22c55e'
})

onMounted(async () => {
  if (auth.isAuthenticated) {
    if (!auth.user) {
      await auth.fetchUser()
    }
    requestPermission()
    await refreshBudget()
  }
  window.addEventListener('ai-budget-changed', refreshBudget)
})

onUnmounted(() => {
  window.removeEventListener('ai-budget-changed', refreshBudget)
})

async function refreshBudget() {
  try {
    Object.assign(aiBudget, await getBudget())
  } catch {
    Object.assign(aiBudget, {
      enabled: false,
      monthly_budget_usd: '0.00',
      usage_usd: '0.00',
      remaining_usd: '0.00',
      percentage_used: '0',
      at_limit: false,
      should_warn: false,
    })
  }
}

watch(
  () => auth.isAuthenticated,
  async (isAuthenticated) => {
    if (isAuthenticated) {
      await refreshBudget()
      return
    }

    Object.assign(aiBudget, {
      enabled: false,
      monthly_budget_usd: '0.00',
      usage_usd: '0.00',
      remaining_usd: '0.00',
      percentage_used: '0',
      at_limit: false,
      should_warn: false,
    })
  },
)

function handleLogout() {
  void auth.logout().finally(() => {
    router.push('/login')
  })
}
</script>

<style scoped>
.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.5rem;
  height: 3.5rem;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
}

.nav-brand a {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--text-primary);
  text-decoration: none;
}

.brand-logo {
  height: 1.75rem;
  width: auto;
}

.nav-links {
  display: flex;
  gap: 1rem;
}

.nav-links a {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.nav-links a.router-link-active {
  color: var(--accent);
}

.nav-user {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.875rem;
}

.ai-budget {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 8rem;
}

.ai-budget-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.ai-budget-track {
  width: 6.25rem;
  height: 0.25rem;
  background: var(--border);
  border-radius: 999px;
  overflow: hidden;
}

.ai-budget-fill {
  height: 100%;
  border-radius: 999px;
}

.main-content {
  padding: 1.5rem;
  max-width: 1280px;
  margin: 0 auto;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  width: 100%;
}
</style>
