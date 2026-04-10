<template>
  <div id="app-layout">
    <nav v-if="auth.isAuthenticated" class="navbar">
      <div class="nav-brand">
        <router-link to="/">Paper Trader</router-link>
      </div>
      <div class="nav-links">
        <router-link to="/">Dashboard</router-link>
        <router-link to="/portfolios">Portfolios</router-link>
        <router-link to="/assets">Assets</router-link>
        <router-link to="/settings">Settings</router-link>
      </div>
      <div class="nav-user">
        <span v-if="auth.user">{{ auth.user.username }}</span>
        <button class="btn btn-secondary btn-sm" @click="handleLogout">Logout</button>
      </div>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

onMounted(() => {
  if (auth.isAuthenticated) {
    auth.fetchUser()
  }
})

function handleLogout() {
  auth.logout()
  router.push('/login')
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
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--text-primary);
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

.main-content {
  padding: 1.5rem;
  max-width: 1280px;
  margin: 0 auto;
}
</style>