<template>
  <div class="card">
    <h3>AI Settings</h3>

    <div v-if="loading" style="text-align: center; padding: 2rem; color: var(--text-secondary);">
      Loading...
    </div>

    <template v-else>
      <div style="margin-bottom: 1.5rem;">
        <label style="display: block; font-size: 0.875rem; margin-bottom: 0.5rem;">Provider</label>
        <div style="display: flex; gap: 0.5rem;">
          <select
            :value="form.provider_name"
            :disabled="isInheritedMode"
            style="flex: 1; padding: 0.5rem; border-radius: 0.25rem; border: 1px solid var(--border);"
            @change="(e) => form.provider_name = (e.target as HTMLSelectElement).value"
          >
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
            <option value="google">Google</option>
          </select>
        </div>
      </div>

      <div style="margin-bottom: 1.5rem;">
        <label style="display: block; font-size: 0.875rem; margin-bottom: 0.5rem;">Usage This Month</label>
        <div style="padding: 0.75rem; border: 1px solid var(--border); border-radius: 0.25rem; background: var(--bg-secondary);">
          <div style="display: flex; justify-content: space-between; gap: 1rem; margin-bottom: 0.5rem; font-size: 0.875rem;">
            <span>{{ budget.usage_usd }} / {{ budget.monthly_budget_usd }} USD</span>
            <span>{{ budget.percentage_used }}%</span>
          </div>
          <div style="height: 0.5rem; background: var(--border); border-radius: 999px; overflow: hidden;">
            <div
              :style="{
                width: `${Math.min(Number(budget.percentage_used || 0), 100)}%`,
                height: '100%',
                background: budgetColor,
              }"
            />
          </div>
          <div style="margin-top: 0.5rem; font-size: 0.75rem; color: var(--text-secondary);">
            Remaining: {{ budget.remaining_usd }} USD
          </div>
        </div>
      </div>

      <div style="margin-bottom: 1.5rem;">
        <label style="display: block; font-size: 0.875rem; margin-bottom: 0.5rem;">
          {{ hasApiKey ? '✓ API Key Configured' : 'API Key' }}
        </label>
        <div style="display: flex; gap: 0.5rem;">
          <input
            v-if="showKeyInput"
            v-model="apiKeyInput"
            type="password"
            placeholder="Paste your API key here"
            style="flex: 1; padding: 0.5rem; border-radius: 0.25rem; border: 1px solid var(--border);"
          />
          <button
            v-if="!showKeyInput"
            class="btn btn-secondary"
            :disabled="isInheritedMode && hasApiKey"
            @click="showKeyInput = true"
          >
            {{ hasApiKey ? 'Update Key' : 'Add Key' }}
          </button>
          <button
            v-else
            class="btn"
            :disabled="!apiKeyInput || savingKey"
            @click="saveApiKey"
          >
            {{ savingKey ? 'Saving...' : 'Save' }}
          </button>
          <button
            v-if="hasApiKey"
            class="btn btn-secondary"
            :disabled="isInheritedMode"
            @click="removeApiKey"
          >
            Remove
          </button>
          <button
            class="btn btn-secondary"
            :disabled="testingConnection || (!hasApiKey && !apiKeyInput) || (isInheritedMode && !apiKeyInput)"
            @click="runConnectionTest"
          >
            {{ testingConnection ? 'Testing...' : 'Test Connection' }}
          </button>
        </div>
        <div style="display: flex; flex-direction: column; gap: 0.35rem; margin-top: 0.75rem; width: 100%;">
          <label
            style="display: grid; grid-template-columns: 1.25rem 1fr; column-gap: 0.5rem; align-items: center; width: 100%; font-size: 0.875rem; line-height: 1; text-align: left;"
            :style="{ opacity: canEditInstanceDefault ? 1 : 0.5 }"
          >
            <input
              v-model="useInstanceDefault"
              type="checkbox"
              :disabled="!canEditInstanceDefault"
              style="width: 1rem; height: 1rem; margin: 0;"
            />
            <span style="min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">Use this key for shared news ingestion on this instance</span>
          </label>
          <label
            style="display: grid; grid-template-columns: 1.25rem 1fr; column-gap: 0.5rem; align-items: center; width: 100%; font-size: 0.875rem; line-height: 1; text-align: left;"
            :style="{ opacity: canEditInstanceDefault && useInstanceDefault ? 1 : 0.5 }"
          >
            <input
              v-model="allowOtherUsers"
              type="checkbox"
              :disabled="!canEditInstanceDefault || !useInstanceDefault"
              style="width: 1rem; height: 1rem; margin: 0;"
            />
            <span style="min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">Allow other users to reuse this key</span>
          </label>
          <div
            v-if="instanceDefaultOwnerUsername"
            class="text-muted"
            style="font-size: 0.75rem;"
          >
            {{ instanceDefaultOwnershipNote }}
          </div>
          <div
            v-if="isInheritedMode"
            class="text-muted"
            style="font-size: 0.75rem;"
          >
            Add your own API key to edit provider, budget, and model settings.
          </div>
        </div>
      </div>

      <div style="margin-bottom: 1.5rem;">
        <label style="display: block; font-size: 0.875rem; margin-bottom: 0.5rem;">Monthly Budget (USD)</label>
        <input
          v-model.number="form.monthly_budget_usd"
          type="number"
          min="1"
          step="0.01"
          :disabled="isInheritedMode"
          style="width: 100%; padding: 0.5rem; border-radius: 0.25rem; border: 1px solid var(--border);"
        />
      </div>

      <div style="margin-bottom: 1.5rem;">
        <label style="display: block; font-size: 0.875rem; margin-bottom: 0.5rem;">Budget Alert Threshold (%)</label>
        <input
          v-model.number="form.alert_threshold_pct"
          type="number"
          min="1"
          max="99"
          :disabled="isInheritedMode"
          style="width: 100%; padding: 0.5rem; border-radius: 0.25rem; border: 1px solid var(--border);"
        />
        <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.25rem;">
          Alert when {{ 100 - form.alert_threshold_pct }}% of budget is consumed
        </div>
      </div>

      <details style="margin-bottom: 1.5rem;" :open="showAdvancedModels" @toggle="showAdvancedModels = ($event.target as HTMLDetailsElement).open">
        <summary style="cursor: pointer; font-size: 0.875rem; font-weight: 500; user-select: none;">
          Advanced: Model Selection by Task
        </summary>
        <div style="display: flex; flex-direction: column; gap: 0.75rem; margin-top: 0.75rem;">
          <div
            v-for="taskName in Object.keys(availableTasks)"
            :key="taskName"
            style="padding: 0.75rem; background: var(--bg-secondary); border-radius: 0.25rem;"
          >
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.5rem;">
              {{ taskName.split('_').map((w: string) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ') }}
            </div>
            <select
              :value="form.task_models[taskName] || getDefaultModel(taskName)"
              :disabled="isInheritedMode"
              style="width: 100%; padding: 0.5rem; border-radius: 0.25rem; border: 1px solid var(--border); font-size: 0.875rem;"
              @change="(e) => updateTaskModel(taskName, (e.target as HTMLSelectElement).value)"
            >
              <option v-for="model in getModelsForProvider()" :key="model" :value="model">
                {{ model }}
              </option>
            </select>
          </div>
        </div>
      </details>

      <button
        class="btn"
        :disabled="saving || isInheritedMode"
        @click="saveSettings"
      >
        {{ saving ? 'Saving...' : 'Save Settings' }}
      </button>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, reactive, onMounted } from 'vue'
import { useToast } from '@/composables/useToast'
import * as aiApi from '@/api/ai'

interface SettingsData {
  provider_name: string
  monthly_budget_usd: string
  alert_threshold_pct: number
  task_models: Record<string, string>
  has_api_key: boolean
  available_tasks: Record<string, Record<string, string>>
  available_models: Record<string, string[]>
  instance_default_enabled: boolean
  instance_default_allow_other_users: boolean
  instance_default_owned_by_current_user: boolean
  instance_default_owner_username: string | null
  can_use_instance_default: boolean
}

interface AISettings {
  provider_name: string
  monthly_budget_usd: number
  alert_threshold_pct: number
  task_models: Record<string, string>
}

const toast = useToast()

const loading = ref(true)
const saving = ref(false)
const savingKey = ref(false)
const testingConnection = ref(false)
const showAdvancedModels = ref(false)
const showKeyInput = ref(false)
const apiKeyInput = ref('')
const hasApiKey = ref(false)
const instanceDefaultEnabled = ref(false)
const canUseInstanceDefault = ref(false)
const useInstanceDefault = ref(false)
const allowOtherUsers = ref(false)
const instanceDefaultOwnedByCurrentUser = ref(false)
const instanceDefaultOwnerUsername = ref<string | null>(null)
const budget = reactive<aiApi.AIBudget>({
  enabled: false,
  monthly_budget_usd: '0.00',
  usage_usd: '0.00',
  remaining_usd: '0.00',
  percentage_used: '0',
  at_limit: false,
  should_warn: false,
})

const form = reactive<AISettings>({
  provider_name: 'openai',
  monthly_budget_usd: 10,
  alert_threshold_pct: 10,
  task_models: {},
})

const availableTasks = ref<Record<string, Record<string, string>>>({})
const availableModels = ref<Record<string, string[]>>({})

onMounted(async () => {
  await Promise.all([loadSettings(), loadBudget()])
})

async function loadSettings() {
  try {
    const data = await aiApi.getSettings() as unknown as SettingsData
    form.provider_name = data.provider_name
    form.monthly_budget_usd = parseFloat(data.monthly_budget_usd)
    form.alert_threshold_pct = data.alert_threshold_pct
    form.task_models = data.task_models || {}
    hasApiKey.value = data.has_api_key
    instanceDefaultEnabled.value = data.instance_default_enabled
    canUseInstanceDefault.value = data.can_use_instance_default
    instanceDefaultOwnedByCurrentUser.value = data.instance_default_owned_by_current_user
    instanceDefaultOwnerUsername.value = data.instance_default_owner_username
    useInstanceDefault.value = !data.instance_default_enabled || data.instance_default_owned_by_current_user
    allowOtherUsers.value = data.instance_default_owned_by_current_user && data.instance_default_allow_other_users

    availableTasks.value = data.available_tasks
    availableModels.value = data.available_models

    loading.value = false
  } catch (error) {
    toast.error('Failed to load AI settings')
    loading.value = false
  }
}

async function loadBudget() {
  try {
    const data = await aiApi.getBudget()
    Object.assign(budget, data)
  } catch {
    Object.assign(budget, {
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

function notifyBudgetChanged() {
  window.dispatchEvent(new Event('ai-budget-changed'))
}

const budgetColor = computed(() => {
  const used = Number(budget.percentage_used || 0)
  if (used >= 100) return '#dc2626'
  if (used >= 100 - form.alert_threshold_pct) return '#f97316'
  if (used >= 50) return '#eab308'
  return '#22c55e'
})

const canEditInstanceDefault = computed(() => {
  return !instanceDefaultEnabled.value || instanceDefaultOwnedByCurrentUser.value
})

const isInheritedMode = computed(() => {
  return !hasApiKey.value && canUseInstanceDefault.value
})

function getModelsForProvider(): string[] {
  return availableModels.value[form.provider_name] || []
}

function getDefaultModel(taskName: string): string {
  const taskKey = taskName.toLowerCase().replace(/ /g, '_')
  const taskModels = availableTasks.value[taskKey as keyof typeof availableTasks.value]
  if (taskModels) {
    return taskModels[form.provider_name] || getModelsForProvider()[0] || ''
  }
  return getModelsForProvider()[0] || ''
}

function updateTaskModel(taskName: string, model: string) {
  form.task_models[taskName] = model
}

async function saveApiKey() {
  if (!apiKeyInput.value) {
    toast.error('Please enter an API key')
    return
  }

  savingKey.value = true
  try {
    await aiApi.setApiKey(apiKeyInput.value, {
      provider_name: form.provider_name,
      use_as_instance_default: useInstanceDefault.value,
      allow_other_users: allowOtherUsers.value,
    })
    apiKeyInput.value = ''
    showKeyInput.value = false
    await loadSettings()
    await loadBudget()
    notifyBudgetChanged()
    toast.success('API key saved successfully')
  } catch (error) {
    toast.error('Failed to save API key')
  } finally {
    savingKey.value = false
  }
}

async function removeApiKey() {
  if (!confirm('Remove API key? You can add it again anytime.')) return

  try {
    await aiApi.removeApiKey()
    await loadSettings()
    await loadBudget()
    notifyBudgetChanged()
    toast.success('API key removed')
  } catch (error) {
    toast.error('Failed to remove API key')
  }
}

async function saveSettings() {
  if (isInheritedMode.value) {
    toast.error('Add your own API key to edit settings')
    return
  }

  saving.value = true
  try {
    await aiApi.updateSettings({
      monthly_budget_usd: form.monthly_budget_usd,
      alert_threshold_pct: form.alert_threshold_pct,
      provider_name: form.provider_name,
      task_models: form.task_models,
    })
    await loadBudget()
    notifyBudgetChanged()
    toast.success('Settings saved')
  } catch (error) {
    toast.error('Failed to save settings')
  } finally {
    saving.value = false
  }
}

async function runConnectionTest() {
  if (isInheritedMode.value && !apiKeyInput.value) {
    toast.error('Add your own API key to test connection')
    return
  }

  testingConnection.value = true
  try {
    const response = await aiApi.testConnection(form.provider_name, apiKeyInput.value || undefined)
    toast.success(`Connection OK (${response.model})`)
  } catch {
    toast.error('Connection test failed')
  } finally {
    testingConnection.value = false
  }
}

const instanceDefaultOwnershipNote = computed(() => {
  if (!instanceDefaultOwnerUsername.value) return ''
  if (instanceDefaultOwnedByCurrentUser.value) {
    return 'This account is using the instance default key.'
  }
  return `Shared instance default key is currently owned by ${instanceDefaultOwnerUsername.value}.`
})
</script>
