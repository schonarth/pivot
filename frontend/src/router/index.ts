import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const portfolioIdRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

function isValidPortfolioId(value: string | string[] | undefined): boolean {
  const id = Array.isArray(value) ? value[0] : value
  if (!id) return false
  return portfolioIdRegex.test(id)
}

function requireValidPortfolioId(to: { params: { id?: string | string[] } }) {
  if (!isValidPortfolioId(to.params.id)) {
    return '/portfolios'
  }
}

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
    },
    {
      path: '/portfolios',
      name: 'portfolios',
      component: () => import('@/views/PortfoliosView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/portfolios/new',
      name: 'portfolio-new',
      component: () => import('@/views/PortfolioNewView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/portfolios/:id',
      name: 'portfolio-detail',
      component: () => import('@/views/PortfolioDetailView.vue'),
      beforeEnter: requireValidPortfolioId,
      props: true,
      meta: { requiresAuth: true },
    },
    {
      path: '/portfolios/:id/trades',
      name: 'portfolio-trades',
      component: () => import('@/views/TradesView.vue'),
      beforeEnter: requireValidPortfolioId,
      props: true,
      meta: { requiresAuth: true },
    },
    {
      path: '/portfolios/:id/trades/new',
      name: 'trade-new',
      component: () => import('@/views/TradeNewView.vue'),
      beforeEnter: requireValidPortfolioId,
      props: true,
      meta: { requiresAuth: true },
    },
    {
      path: '/portfolios/:id/alerts',
      name: 'portfolio-alerts',
      component: () => import('@/views/AlertsView.vue'),
      beforeEnter: requireValidPortfolioId,
      props: true,
      meta: { requiresAuth: true },
    },
    {
      path: '/portfolios/:id/strategies',
      name: 'portfolio-strategies',
      component: () => import('@/views/StrategiesView.vue'),
      beforeEnter: requireValidPortfolioId,
      props: true,
      meta: { requiresAuth: true },
    },
    {
      path: '/assets',
      name: 'assets',
      component: () => import('@/views/AssetsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/assets/:symbol',
      name: 'asset-detail',
      component: () => import('@/views/AssetDetailView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/views/SettingsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/settings/ai',
      name: 'settings-ai',
      component: () => import('@/views/SettingsView.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  await auth.initialize({ forceRefresh: !!to.meta.requiresAuth })
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
})

export default router
