<template>
  <div class="card">
    <h3>MCP Access</h3>
    <div style="margin-bottom: 1.5rem;">
      <label style="display: block; font-size: 0.875rem; margin-bottom: 0.5rem;">Tell MCP Server Your Authentication Details</label>
      <div style="display: flex; gap: 0.5rem; align-items: center;">
        <textarea
          :value="authPrompt"
          readonly
          style="flex: 1; padding: 0.5rem; border-radius: 0.25rem; border: 1px solid var(--border); background: var(--bg-secondary); font-family: monospace; font-size: 0.75rem; resize: none; min-height: 4rem; line-height: 1.4;"
        />
        <button
          class="btn btn-secondary"
          style="padding: 0.5rem 1rem; white-space: nowrap;"
          @click="copyPrompt"
        >
          Copy
        </button>
      </div>
    </div>

    <div style="margin-bottom: 1.5rem;">
      <label style="display: block; font-size: 0.875rem; margin-bottom: 0.5rem;">One-Time Password</label>
      <button
        class="btn"
        :disabled="otpLoading"
        style="width: 100%;"
        @click="generateOTP"
      >
        {{ otpLoading ? 'Generating...' : 'Generate OTP' }}
      </button>
      <div
        v-if="otpCode"
        style="margin-top: 0.75rem; padding: 0.75rem; background: var(--bg-secondary); border-radius: 0.25rem;"
      >
        <div style="font-family: monospace; font-size: 1.25rem; font-weight: bold; letter-spacing: 0.25em; text-align: center; margin-bottom: 0.5rem;">
          {{ otpCode }}
        </div>
        <div style="font-size: 0.75rem; color: var(--text-secondary);">
          Expires in {{ otpTimeLeft }}s
        </div>
      </div>
    </div>

    <div>
      <label style="display: block; font-size: 0.875rem; margin-bottom: 0.75rem;">Authenticated Agents</label>
      <div
        v-if="agents.length === 0"
        style="padding: 1rem; text-align: center; color: var(--text-secondary); font-size: 0.875rem;"
      >
        No agents connected
      </div>
      <div
        v-else
        style="display: flex; flex-direction: column; gap: 0.75rem;"
      >
        <div
          v-for="agent in agents"
          :key="agent.id"
          style="padding: 0.75rem; background: var(--bg-secondary); border-radius: 0.25rem; display: flex; justify-content: space-between; align-items: center;"
        >
          <div style="flex: 1;">
            <div style="font-weight: 500; font-size: 0.875rem;">
              {{ agent.name }}
            </div>
            <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.25rem;">
              {{ agent.origin }} · {{ formatDate(agent.created_at) }}
            </div>
          </div>
          <button
            class="btn btn-secondary"
            style="padding: 0.5rem 1rem; white-space: nowrap;"
            @click="revokeAgent(agent.id)"
          >
            Revoke
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import * as mcpApi from '@/api/mcp'
import type { MCPAgent } from '@/api/mcp'

const auth = useAuthStore()
const toast = useToast()

const userID = ref('')
const agents = ref<MCPAgent[]>([])
const otpCode = ref('')
const otpTimeLeft = ref(60)
const otpLoading = ref(false)
let otpInterval: number | null = null

const authPrompt = computed(
  () => `Please find my paper trader app MCP server at http://localhost:8000/api/mcp/ and authenticate. UUID: ${userID.value}`
)

onMounted(async () => {
  userID.value = auth.user?.api_uuid || ''
  await loadAgents()
})

onUnmounted(() => {
  if (otpInterval) clearInterval(otpInterval)
})

async function generateOTP() {
  otpLoading.value = true
  try {
    const response = await mcpApi.generateOTP()
    otpCode.value = response.code
    otpTimeLeft.value = 60

    navigator.clipboard.writeText(otpCode.value)

    if (otpInterval) clearInterval(otpInterval)
    otpInterval = window.setInterval(() => {
      otpTimeLeft.value--
      if (otpTimeLeft.value <= 0) {
        clearInterval(otpInterval!)
        otpInterval = null
        otpCode.value = ''
      }
    }, 1000)

    toast.success('OTP generated and copied to clipboard')
  } catch (error) {
    toast.error('Failed to generate OTP')
  } finally {
    otpLoading.value = false
  }
}

async function loadAgents() {
  try {
    agents.value = await mcpApi.listAgents()
  } catch (error) {
    toast.error('Failed to load agents')
  }
}

async function revokeAgent(agentID: string) {
  try {
    await mcpApi.revokeAgent(agentID)
    agents.value = agents.value.filter(a => a.id !== agentID)
    toast.success('Agent revoked')
  } catch (error) {
    toast.error('Failed to revoke agent')
  }
}

function copyPrompt() {
  navigator.clipboard.writeText(authPrompt.value)
  toast.success('Prompt copied to clipboard')
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}
</script>
