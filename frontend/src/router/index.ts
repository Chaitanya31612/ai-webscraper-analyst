/**
 * Vue Router Configuration
 *
 * Public routes:  /  /login  /register
 * Protected:      /dashboard (and all sub-routes)
 */

import { createRouter, createWebHistory } from 'vue-router'

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
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { requiresAuth: false }, // flip to true once auth is wired
    },
  ],
  scrollBehavior(_to, _from, savedPosition) {
    return savedPosition || { top: 0, behavior: 'smooth' }
  },
})

// ---------------------------------------------------------------------------
// Navigation Guard — auth check (placeholder, activates with requiresAuth)
// ---------------------------------------------------------------------------
router.beforeEach((to, _from, next) => {
  const requiresAuth = to.meta.requiresAuth
  const token = localStorage.getItem('auth_token')

  if (requiresAuth && !token) {
    next({ name: 'login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
})

export default router
