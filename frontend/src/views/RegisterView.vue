<template>
  <div class="auth-container">
    <div class="card" style="max-width: 400px; margin: 4rem auto;">
      <h2 style="margin-bottom: 1.5rem;">Register</h2>
      <div v-if="error" class="alert-danger">{{ error }}</div>
      <div class="form-group">
        <label for="username">Username</label>
        <input id="username" v-model="username" type="text" autocomplete="username" required />
      </div>
      <div class="form-group">
        <label for="email">Email</label>
        <input id="email" v-model="email" type="email" autocomplete="email" required />
      </div>
      <div class="form-group">
        <label for="password">Password</label>
        <input id="password" v-model="password" type="password" autocomplete="new-password" required minlength="8" />
      </div>
      <button class="btn" style="width: 100%;" :disabled="loading" @click="handleRegister">
        <span v-if="loading" class="spinner"></span>
        Register
      </button>
      <p style="margin-top: 1rem; text-align: center; font-size: 0.875rem;">
        Already have an account? <router-link to="/login">Login</router-link>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const username = ref('')
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleRegister() {
  error.value = ''
  loading.value = true
  try {
    await auth.register(username.value, email.value, password.value)
    router.push('/')
  } catch (e: any) {
    error.value = e.response?.data?.error?.message || 'Registration failed'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-container { min-height: 100vh; }
.alert-danger { background: rgba(239,68,68,0.15); color: var(--danger); padding: 0.75rem; border-radius: 6px; margin-bottom: 1rem; }
</style>