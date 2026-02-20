/**
 * Vue Router Configuration
 *
 * Default routes: /  /login  /register  /dashboard
 * Auth:           /login and /register redirect away if already logged in
 * Protected:      /dashboard requires auth
 * OAuth:          /auth/google/callback handles Google redirect
 */

import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomeView.vue'),
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { guestOnly: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { guestOnly: true },
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/auth/google/callback',
      name: 'google-callback',
      component: () => import('@/views/GoogleCallbackView.vue'),
    },

    // --- Legacy Placeholder design (v0) ---
    {
      path: '/v0',
      name: 'legacy-home',
      component: () => import('@/views/HomeView.vue'),
    },
  ],
  scrollBehavior(_to, _from, savedPosition) {
    return savedPosition || { top: 0, behavior: 'smooth' }
  },
})

// ---------------------------------------------------------------------------
// Navigation Guard — auth check
// ---------------------------------------------------------------------------
router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()
  const isAuthenticated = authStore.isAuthenticated

  // Protected route — redirect to login if not authenticated
  if (to.meta.requiresAuth && !isAuthenticated) {
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }

  // Guest-only route — redirect to dashboard if already logged in
  if (to.meta.guestOnly && isAuthenticated) {
    next({ name: 'dashboard' })
    return
  }

  next()
})

export default router
